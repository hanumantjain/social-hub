from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from database import get_db
from models.user import User
from models.post import Post
from schemas.post import PostResponse
from routers.auth import get_current_user
from utils.s3 import s3_handler
from logger import logger
from pathlib import Path
from typing import List
from pydantic import BaseModel

router = APIRouter()

# Pydantic models for presigned URL workflow
class PresignedUrlRequest(BaseModel):
    filename: str
    content_type: str

class PresignedUrlResponse(BaseModel):
    upload_url: str
    key: str
    public_url: str

class ConfirmUploadRequest(BaseModel):
    image_url: str
    title: str = ""
    caption: str = ""
    tags: list[str] = []

# Allowed file extensions
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}

# Allowed MIME types
ALLOWED_MIME_TYPES = {
    "image/jpeg", "image/jpg", "image/png", 
    "image/gif", "image/webp"
}

def is_allowed_file(filename: str, content_type: str) -> bool:
    """Check if file extension and MIME type are allowed"""
    has_valid_extension = Path(filename).suffix.lower() in ALLOWED_EXTENSIONS
    has_valid_mime = content_type in ALLOWED_MIME_TYPES
    return has_valid_extension and has_valid_mime

@router.post("/presigned-url", response_model=PresignedUrlResponse)
async def get_presigned_upload_url(
    request: PresignedUrlRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Generate a pre-signed URL for direct S3 upload from the browser.
    This bypasses API Gateway's 10MB limit for large files.
    """
    logger.info(f"Presigned URL request by user: {current_user.username} for file: {request.filename}")
    
    # Validate file type
    if not is_allowed_file(request.filename, request.content_type):
        logger.warning(f"Invalid file type: {request.filename} ({request.content_type})")
        raise HTTPException(
            status_code=400,
            detail=f"File type not allowed. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}"
        )
    
    try:
        # Generate pre-signed URL
        presigned_data = s3_handler.generate_presigned_upload_url(
            filename=request.filename,
            content_type=request.content_type
        )
        
        logger.info(f"Generated presigned URL for {current_user.username}: {presigned_data['key']}")
        
        return PresignedUrlResponse(**presigned_data)
        
    except Exception as e:
        logger.error(f"Failed to generate presigned URL: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate upload URL: {str(e)}")

@router.post("/confirm-upload", response_model=PostResponse)
async def confirm_upload(
    request: ConfirmUploadRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Confirm that the file was uploaded to S3 and create the post record.
    This is called after the frontend successfully uploads directly to S3.
    """
    logger.info(f"Upload confirmation by user: {current_user.username} for: {request.image_url}")
    
    try:
        # Create post record
        tags_str = ",".join(request.tags) if request.tags else None
        db_post = Post(
            user_id=current_user.id,
            image_url=request.image_url,
            title=request.title if request.title else None,
            caption=request.caption if request.caption else None,
            tags=tags_str
        )
        
        db.add(db_post)
        db.commit()
        db.refresh(db_post)
        
        logger.info(f"Post created successfully: ID={db_post.id} by {current_user.username}")
        
        # Prepare response with user info
        response = PostResponse(
            id=db_post.id,
            user_id=db_post.user_id,
            image_url=db_post.image_url,
            title=db_post.title,
            caption=db_post.caption,
            tags=db_post.tags,
            views=db_post.views or 0,
            downloads=db_post.downloads or 0,
            created_at=db_post.created_at,
            updated_at=db_post.updated_at,
            username=current_user.username,
            user_full_name=current_user.full_name
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Failed to create post: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create post: {str(e)}")

@router.post("/upload", response_model=PostResponse)
async def upload_post(
    file: UploadFile = File(...),
    title: str = Form(""),
    caption: str = Form(""),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Upload a new post with image to S3"""
    logger.info(f"Upload attempt by user: {current_user.username}")
    
    # Debug: Check S3 configuration
    logger.info(f"S3 bucket: {s3_handler.bucket_name}")
    logger.info(f"S3 region: {s3_handler.region}")
    
    # Validate file
    if not file.filename:
        logger.warning(f"Upload failed: No file provided by {current_user.username}")
        raise HTTPException(status_code=400, detail="No file provided")
    
    if not is_allowed_file(file.filename, file.content_type or ""):
        logger.warning(f"Upload failed: Invalid file type {file.filename} ({file.content_type}) by {current_user.username}")
        raise HTTPException(
            status_code=400,
            detail=f"File type not allowed. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}"
        )
    
    # Check file size (max 5MB for API Gateway compatibility)
    file.file.seek(0, 2)  # Seek to end
    file_size = file.file.tell()
    file.file.seek(0)  # Reset to beginning
    
    if file_size > 5 * 1024 * 1024:  # 5MB
        logger.warning(f"Upload failed: File too large ({file_size} bytes) by {current_user.username}")
        raise HTTPException(status_code=400, detail="File size must be less than 5MB")
    
    try:
        # Upload to S3
        logger.info(f"Attempting to upload to S3 bucket: {s3_handler.bucket_name}")
        image_url = s3_handler.upload_file(
            file.file,
            file.filename,
            file.content_type or "image/jpeg"
        )
        
        if not image_url:
            logger.error(f"S3 upload returned None for {current_user.username}")
            raise HTTPException(status_code=500, detail="Failed to upload image to S3")
        
        logger.info(f"File uploaded to S3 successfully: {image_url}")
        
        # Create post record
        db_post = Post(
            user_id=current_user.id,
            image_url=image_url,
            title=title if title else None,
            caption=caption if caption else None
        )
        db.add(db_post)
        db.commit()
        db.refresh(db_post)
        
        logger.info(f"Post created successfully: ID {db_post.id} by {current_user.username}")
        
        # Prepare response with user info
        response = PostResponse(
            id=db_post.id,
            user_id=db_post.user_id,
            image_url=db_post.image_url,
            title=db_post.title,
            caption=db_post.caption,
            tags=db_post.tags,
            views=db_post.views or 0,
            downloads=db_post.downloads or 0,
            created_at=db_post.created_at,
            updated_at=db_post.updated_at,
            username=current_user.username,
            user_full_name=current_user.full_name
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        logger.error(f"Upload failed for {current_user.username}: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@router.get("/", response_model=List[PostResponse])
async def get_all_posts(
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """Get all posts (feed)"""
    logger.info(f"Fetching posts: skip={skip}, limit={limit}")
    
    try:
        posts = db.query(Post).order_by(Post.created_at.desc()).offset(skip).limit(limit).all()
        
        # Add user info to each post
        response = []
        for post in posts:
            user = db.query(User).filter(User.id == post.user_id).first()
            try:
                response.append(PostResponse(
                    id=post.id,
                    user_id=post.user_id,
                    image_url=post.image_url,
                    title=getattr(post, 'title', None),
                    caption=post.caption,
                    tags=getattr(post, 'tags', None),
                    views=getattr(post, 'views', 0) or 0,
                    downloads=getattr(post, 'downloads', 0) or 0,
                    created_at=post.created_at,
                    updated_at=post.updated_at,
                    username=user.username if user else None,
                    user_full_name=user.full_name if user else None
                ))
            except Exception as e:
                logger.error(f"Error processing post {post.id}: {str(e)}")
                # Skip this post if there's an error
                continue
        
        logger.info(f"Returned {len(response)} posts")
        return response
    except Exception as e:
        logger.error(f"Error fetching posts: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch posts: {str(e)}")

@router.get("/{post_id}", response_model=PostResponse)
async def get_post_by_id(
    post_id: int,
    db: Session = Depends(get_db)
):
    """Get a single post by ID"""
    logger.info(f"Fetching post: {post_id}")
    
    try:
        post = db.query(Post).filter(Post.id == post_id).first()
        if not post:
            logger.warning(f"Post {post_id} not found")
            raise HTTPException(status_code=404, detail="Post not found")
        
        user = db.query(User).filter(User.id == post.user_id).first()
        
        response = PostResponse(
            id=post.id,
            user_id=post.user_id,
            image_url=post.image_url,
            title=getattr(post, 'title', None),
            caption=post.caption,
            tags=getattr(post, 'tags', None),
            views=getattr(post, 'views', 0) or 0,
            downloads=getattr(post, 'downloads', 0) or 0,
            created_at=post.created_at,
            updated_at=post.updated_at,
            username=user.username if user else None,
            user_full_name=user.full_name if user else None
        )
        
        return response
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching post {post_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch post: {str(e)}")

@router.post("/{post_id}/view")
async def increment_view(
    post_id: int,
    db: Session = Depends(get_db)
):
    """Increment view count for a post"""
    logger.info(f"Incrementing view for post: {post_id}")
    
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    post.views = (post.views or 0) + 1
    db.commit()
    db.refresh(post)
    
    return {"views": post.views}

@router.post("/{post_id}/download")
async def increment_download(
    post_id: int,
    db: Session = Depends(get_db)
):
    """Increment download count for a post"""
    logger.info(f"Incrementing download for post: {post_id}")
    
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    post.downloads = (post.downloads or 0) + 1
    db.commit()
    db.refresh(post)
    
    return {"downloads": post.downloads}

@router.delete("/{post_id}")
async def delete_post(
    post_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a post (only by owner)"""
    logger.info(f"Delete request for post {post_id} by {current_user.username}")
    
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        logger.warning(f"Post {post_id} not found")
        raise HTTPException(status_code=404, detail="Post not found")
    
    if post.user_id != current_user.id:
        logger.warning(f"Unauthorized delete attempt: post {post_id} by {current_user.username}")
        raise HTTPException(status_code=403, detail="Not authorized to delete this post")
    
    # Delete file from S3
    if post.image_url:
        deleted = s3_handler.delete_file(post.image_url)
        if deleted:
            logger.info(f"Deleted file from S3: {post.image_url}")
        else:
            logger.warning(f"Failed to delete file from S3: {post.image_url}")
    
    # Delete post record
    db.delete(post)
    db.commit()
    
    logger.info(f"Post {post_id} deleted successfully by {current_user.username}")
    return {"message": "Post deleted successfully"}

