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
    caption: str = ""

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
        db_post = Post(
            user_id=current_user.id,
            image_url=request.image_url,
            caption=request.caption if request.caption else None
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
            caption=db_post.caption,
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
    caption: str = Form(""),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Upload a new post with image to S3"""
    logger.info(f"Upload attempt by user: {current_user.username}")
    
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
    
    # Check file size (max 8MB for API Gateway compatibility)
    file.file.seek(0, 2)  # Seek to end
    file_size = file.file.tell()
    file.file.seek(0)  # Reset to beginning
    
    if file_size > 8 * 1024 * 1024:  # 8MB
        logger.warning(f"Upload failed: File too large ({file_size} bytes) by {current_user.username}")
        raise HTTPException(status_code=400, detail="File size must be less than 8MB")
    
    try:
        # Upload to S3
        image_url = s3_handler.upload_file(
            file.file,
            file.filename,
            file.content_type or "image/jpeg"
        )
        
        if not image_url:
            logger.error(f"S3 upload failed for {current_user.username}")
            raise HTTPException(status_code=500, detail="Failed to upload image to S3")
        
        logger.info(f"File uploaded to S3: {image_url}")
        
        # Create post record
        db_post = Post(
            user_id=current_user.id,
            image_url=image_url,
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
            caption=db_post.caption,
            created_at=db_post.created_at,
            updated_at=db_post.updated_at,
            username=current_user.username,
            user_full_name=current_user.full_name
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload failed for {current_user.username}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to upload image")

@router.get("/", response_model=List[PostResponse])
async def get_all_posts(
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """Get all posts (feed)"""
    logger.info(f"Fetching posts: skip={skip}, limit={limit}")
    
    posts = db.query(Post).order_by(Post.created_at.desc()).offset(skip).limit(limit).all()
    
    # Add user info to each post
    response = []
    for post in posts:
        user = db.query(User).filter(User.id == post.user_id).first()
        response.append(PostResponse(
            id=post.id,
            user_id=post.user_id,
            image_url=post.image_url,
            caption=post.caption,
            created_at=post.created_at,
            updated_at=post.updated_at,
            username=user.username if user else None,
            user_full_name=user.full_name if user else None
        ))
    
    logger.info(f"Returned {len(response)} posts")
    return response

@router.get("/debug/test-s3-write")
async def test_s3_write(current_user: User = Depends(get_current_user)):
    """Debug endpoint to test direct S3 write from Lambda"""
    import io
    try:
        # Try to write a test file
        test_content = io.BytesIO(b"test content from lambda")
        test_url = s3_handler.upload_file(
            test_content,
            "test-lambda-write.txt",
            "text/plain"
        )
        return {
            "success": True,
            "message": "Lambda can write to S3",
            "test_url": test_url
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Lambda CANNOT write to S3"
        }

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

