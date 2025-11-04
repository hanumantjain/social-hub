from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import text
from database import get_db, engine, Base
from routers.auth import router as auth_router
from routers.posts import router as posts_router
from models import *
from middleware import RequestLoggingMiddleware
from logger import logger
from dotenv import load_dotenv
from mangum import Mangum
import os

# Load environment variables (locally)
load_dotenv()

app = FastAPI()

def run_migrations():
    """Run database migrations on startup"""
    with engine.begin() as connection:  # Use begin() for auto-commit/rollback
        try:
            # Check if bio column exists
            result = connection.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='users' AND column_name='bio'
            """))
            
            if result.fetchone() is None:
                # Column doesn't exist, add it
                connection.execute(text("""
                    ALTER TABLE users 
                    ADD COLUMN bio VARCHAR NULL
                """))
                logger.info("✅ Migration: Added 'bio' column to users table")
            else:
                logger.info("✅ Migration: 'bio' column already exists")
            
            # Check if views column exists in posts table
            result = connection.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='posts' AND column_name='views'
            """))
            
            if result.fetchone() is None:
                # Column doesn't exist, add it
                connection.execute(text("""
                    ALTER TABLE posts 
                    ADD COLUMN views INTEGER NOT NULL DEFAULT 0
                """))
                logger.info("✅ Migration: Added 'views' column to posts table")
            else:
                logger.info("✅ Migration: 'views' column already exists")
            
            # Check if downloads column exists in posts table
            result = connection.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='posts' AND column_name='downloads'
            """))
            
            if result.fetchone() is None:
                # Column doesn't exist, add it
                connection.execute(text("""
                    ALTER TABLE posts 
                    ADD COLUMN downloads INTEGER NOT NULL DEFAULT 0
                """))
                logger.info("✅ Migration: Added 'downloads' column to posts table")
            else:
                logger.info("✅ Migration: 'downloads' column already exists")
            
            # Check if title column exists in posts table
            result = connection.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='posts' AND column_name='title'
            """))
            
            if result.fetchone() is None:
                # Column doesn't exist, add it
                connection.execute(text("""
                    ALTER TABLE posts 
                    ADD COLUMN title VARCHAR NULL
                """))
                logger.info("✅ Migration: Added 'title' column to posts table")
            else:
                logger.info("✅ Migration: 'title' column already exists")
            
            # Check if tags column exists in posts table
            result = connection.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='posts' AND column_name='tags'
            """))
            
            if result.fetchone() is None:
                # Column doesn't exist, add it
                connection.execute(text("""
                    ALTER TABLE posts 
                    ADD COLUMN tags VARCHAR NULL
                """))
                logger.info("✅ Migration: Added 'tags' column to posts table")
            else:
                logger.info("✅ Migration: 'tags' column already exists")
                
        except Exception as e:
            logger.error(f"❌ Migration failed: {e}")
            import traceback
            logger.error(f"Migration traceback: {traceback.format_exc()}")
            raise  # Re-raise to ensure we know migrations failed

@app.on_event("startup")
async def startup_event():
    logger.info("Lambda cold start: initializing FastAPI application")
    
    # Run migrations FIRST before creating tables
    logger.info("Running database migrations...")
    try:
        run_migrations()
        logger.info("Migrations complete!")
    except Exception as e:
        logger.error(f"Migration error: {str(e)}")
        # Continue anyway - migrations might have already run
    
    logger.info("Creating database tables...")
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database initialization complete!")
    except Exception as e:
        logger.error(f"Table creation error: {str(e)}")
        # Continue anyway - tables might already exist

# Add Request Logging Middleware (should be first)
app.add_middleware(RequestLoggingMiddleware)

# CORS configuration
cors_origins = [
    "http://localhost:5173",
    "https://social.hanumantjain.tech",
    "https://fg5373zzn7.execute-api.us-east-1.amazonaws.com",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Routers
app.include_router(auth_router, prefix="/auth", tags=["authentication"])
app.include_router(posts_router, prefix="/posts", tags=["posts"])

# Explicit OPTIONS handler for CORS preflight
@app.options("/{full_path:path}")
async def options_handler(full_path: str):
    """Handle preflight OPTIONS requests for CORS"""
    from fastapi import Response
    response = Response()
    response.headers["Access-Control-Allow-Origin"] = "https://social.hanumantjain.tech"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS, PATCH"
    response.headers["Access-Control-Allow-Headers"] = "*"
    response.headers["Access-Control-Allow-Credentials"] = "true"
    return response

@app.get("/")
def read_root():
    return {"message": "Hello from FastAPI on AWS Lambda"}

@app.get("/api/posts/{post_id}")
def get_post_by_id_workaround(post_id: int, db: Session = Depends(get_db)):
    """Temporary workaround endpoint for getting a single post by ID"""
    from fastapi import HTTPException
    
    try:
        # Check which columns exist
        columns_check = db.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='posts'
        """))
        existing_columns = {row[0] for row in columns_check}
        
        # Build SELECT clause
        select_fields = ["p.id", "p.user_id", "p.image_url", "p.caption", "p.created_at", "p.updated_at"]
        
        if 'title' in existing_columns:
            select_fields.append("p.title")
        if 'tags' in existing_columns:
            select_fields.append("p.tags")
        if 'views' in existing_columns:
            select_fields.append("COALESCE(p.views, 0) as views")
        else:
            select_fields.append("0 as views")
        if 'downloads' in existing_columns:
            select_fields.append("COALESCE(p.downloads, 0) as downloads")
        else:
            select_fields.append("0 as downloads")
        
        select_clause = ", ".join(select_fields)
        
        query = f"""
            SELECT 
                {select_clause},
                u.username,
                u.full_name as user_full_name
            FROM posts p
            LEFT JOIN users u ON p.user_id = u.id
            WHERE p.id = :post_id
        """
        
        result = db.execute(text(query), {"post_id": post_id}).first()
        
        if not result:
            raise HTTPException(status_code=404, detail="Post not found")
        
        post_dict = {
            "id": result.id,
            "user_id": result.user_id,
            "username": result.username if hasattr(result, 'username') else None,
            "user_full_name": result.user_full_name if hasattr(result, 'user_full_name') else None,
            "image_url": result.image_url,
            "caption": result.caption,
            "views": result.views if hasattr(result, 'views') else 0,
            "downloads": result.downloads if hasattr(result, 'downloads') else 0,
            "created_at": result.created_at.isoformat() if result.created_at else None,
            "updated_at": result.updated_at.isoformat() if result.updated_at else None
        }
        
        if 'title' in existing_columns:
            post_dict["title"] = getattr(result, 'title', None)
        if 'tags' in existing_columns:
            post_dict["tags"] = getattr(result, 'tags', None)
        
        return post_dict
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching post {post_id}: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch post: {str(e)}")

@app.get("/api/posts")
def get_posts_workaround(db: Session = Depends(get_db)):
    """Temporary workaround endpoint for getting posts"""
    try:
        # Check which columns exist in the posts table
        columns_check = db.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='posts'
        """))
        existing_columns = {row[0] for row in columns_check}
        
        # Build SELECT clause based on existing columns
        select_fields = ["p.id", "p.user_id", "p.image_url", "p.caption", "p.created_at", "p.updated_at"]
        
        if 'title' in existing_columns:
            select_fields.append("p.title")
        if 'tags' in existing_columns:
            select_fields.append("p.tags")
        if 'views' in existing_columns:
            select_fields.append("COALESCE(p.views, 0) as views")
        else:
            select_fields.append("0 as views")
        if 'downloads' in existing_columns:
            select_fields.append("COALESCE(p.downloads, 0) as downloads")
        else:
            select_fields.append("0 as downloads")
        
        select_clause = ", ".join(select_fields)
        
        # Use raw SQL to safely query posts
        query = f"""
            SELECT 
                {select_clause},
                u.username,
                u.full_name as user_full_name
            FROM posts p
            LEFT JOIN users u ON p.user_id = u.id
            ORDER BY p.created_at DESC
            LIMIT 20
        """
        
        result = db.execute(text(query))
        
        posts_list = []
        for row in result:
            post_dict = {
                "id": row.id,
                "user_id": row.user_id,
                "username": row.username if hasattr(row, 'username') else None,
                "user_full_name": row.user_full_name if hasattr(row, 'user_full_name') else None,
                "image_url": row.image_url,
                "caption": row.caption,
                "views": row.views if hasattr(row, 'views') else 0,
                "downloads": row.downloads if hasattr(row, 'downloads') else 0,
                "created_at": row.created_at.isoformat() if row.created_at else None,
                "updated_at": row.updated_at.isoformat() if row.updated_at else None
            }
            
            # Add optional fields if they exist
            if 'title' in existing_columns:
                post_dict["title"] = getattr(row, 'title', None)
            if 'tags' in existing_columns:
                post_dict["tags"] = getattr(row, 'tags', None)
            
            posts_list.append(post_dict)
        
        return posts_list
    except Exception as e:
        logger.error(f"Error fetching posts: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        from fastapi import HTTPException
        raise HTTPException(status_code=500, detail=f"Failed to fetch posts: {str(e)}")

@app.get("/api/posts/user/{user_id}")
def get_user_posts_workaround(user_id: int, db: Session = Depends(get_db)):
    """Temporary workaround endpoint for getting user posts"""
    from fastapi import HTTPException
    
    try:
        # Check which columns exist
        columns_check = db.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='posts'
        """))
        existing_columns = {row[0] for row in columns_check}
        
        # Build SELECT clause
        select_fields = ["p.id", "p.user_id", "p.image_url", "p.caption", "p.created_at", "p.updated_at"]
        
        if 'title' in existing_columns:
            select_fields.append("p.title")
        if 'tags' in existing_columns:
            select_fields.append("p.tags")
        if 'views' in existing_columns:
            select_fields.append("COALESCE(p.views, 0) as views")
        else:
            select_fields.append("0 as views")
        if 'downloads' in existing_columns:
            select_fields.append("COALESCE(p.downloads, 0) as downloads")
        else:
            select_fields.append("0 as downloads")
        
        select_clause = ", ".join(select_fields)
        
        query = f"""
            SELECT 
                {select_clause},
                u.username,
                u.full_name as user_full_name
            FROM posts p
            LEFT JOIN users u ON p.user_id = u.id
            WHERE p.user_id = :user_id
            ORDER BY p.created_at DESC
        """
        
        result = db.execute(text(query), {"user_id": user_id})
        
        posts_list = []
        for row in result:
            post_dict = {
                "id": row.id,
                "user_id": row.user_id,
                "username": row.username if hasattr(row, 'username') else None,
                "user_full_name": row.user_full_name if hasattr(row, 'user_full_name') else None,
                "image_url": row.image_url,
                "caption": row.caption,
                "views": row.views if hasattr(row, 'views') else 0,
                "downloads": row.downloads if hasattr(row, 'downloads') else 0,
                "created_at": row.created_at.isoformat() if row.created_at else None,
                "updated_at": row.updated_at.isoformat() if row.updated_at else None
            }
            
            if 'title' in existing_columns:
                post_dict["title"] = getattr(row, 'title', None)
            if 'tags' in existing_columns:
                post_dict["tags"] = getattr(row, 'tags', None)
            
            posts_list.append(post_dict)
        
        return posts_list
    except Exception as e:
        logger.error(f"Error fetching user posts: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch user posts: {str(e)}")

@app.post("/api/posts/{post_id}/view")
def track_view_workaround(post_id: int, db: Session = Depends(get_db)):
    """Track a view for a post"""
    from fastapi import HTTPException
    
    try:
        # Check if views column exists
        columns_check = db.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='posts' AND column_name='views'
        """))
        
        if columns_check.fetchone() is None:
            # Column doesn't exist, run migrations first
            try:
                run_migrations()
            except Exception as e:
                logger.error(f"Failed to run migrations: {str(e)}")
        
        # Check if post exists
        post_check = db.execute(text("SELECT id FROM posts WHERE id = :post_id"), {"post_id": post_id}).first()
        if not post_check:
            raise HTTPException(status_code=404, detail="Post not found")
        
        # Update views
        db.execute(text("""
            UPDATE posts 
            SET views = COALESCE(views, 0) + 1 
            WHERE id = :post_id
        """), {"post_id": post_id})
        db.commit()
        
        # Get updated views count
        views_result = db.execute(text("SELECT COALESCE(views, 0) as views FROM posts WHERE id = :post_id"), {"post_id": post_id}).first()
        views = views_result.views if views_result else 0
        
        return {"views": views}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error tracking view: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to track view: {str(e)}")

@app.post("/api/posts/{post_id}/download")
def track_download_workaround(post_id: int, db: Session = Depends(get_db)):
    """Track a download for a post"""
    from fastapi import HTTPException
    
    try:
        # Check if downloads column exists
        columns_check = db.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='posts' AND column_name='downloads'
        """))
        
        if columns_check.fetchone() is None:
            # Column doesn't exist, run migrations first
            try:
                run_migrations()
            except Exception as e:
                logger.error(f"Failed to run migrations: {str(e)}")
        
        # Check if post exists
        post_check = db.execute(text("SELECT id FROM posts WHERE id = :post_id"), {"post_id": post_id}).first()
        if not post_check:
            raise HTTPException(status_code=404, detail="Post not found")
        
        # Update downloads
        db.execute(text("""
            UPDATE posts 
            SET downloads = COALESCE(downloads, 0) + 1 
            WHERE id = :post_id
        """), {"post_id": post_id})
        db.commit()
        
        # Get updated downloads count
        downloads_result = db.execute(text("SELECT COALESCE(downloads, 0) as downloads FROM posts WHERE id = :post_id"), {"post_id": post_id}).first()
        downloads = downloads_result.downloads if downloads_result else 0
        
        return {"downloads": downloads}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error tracking download: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to track download: {str(e)}")

@app.get("/health")
def health_check(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        return {"status": "Database connection successful"}
    except Exception as e:
        return {"status": "Database connection failed", "error": str(e)}

# Lambda handler with CORS support
handler = Mangum(app, lifespan="off")
#
