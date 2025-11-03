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
    with engine.connect() as connection:
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
                connection.commit()
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
                connection.commit()
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
                connection.commit()
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
                connection.commit()
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
                connection.commit()
                logger.info("✅ Migration: Added 'tags' column to posts table")
            else:
                logger.info("✅ Migration: 'tags' column already exists")
                
        except Exception as e:
            logger.error(f"❌ Migration failed: {e}")
            connection.rollback()

@app.on_event("startup")
async def startup_event():
    logger.info("Lambda cold start: initializing FastAPI application")
    logger.info("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database initialization complete!")
    
    # Run migrations
    logger.info("Running database migrations...")
    run_migrations()
    logger.info("Migrations complete!")

# Add Request Logging Middleware (should be first)
app.add_middleware(RequestLoggingMiddleware)

# CORS configuration
cors_origins = [
    "http://localhost:5173",
    "https://social.hanumantjain.tech",
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
    return {"message": "OK"}

@app.get("/")
def read_root():
    return {"message": "Hello from FastAPI on AWS Lambda"}

@app.get("/api/posts/{post_id}")
def get_post_by_id_workaround(post_id: int, db: Session = Depends(get_db)):
    """Temporary workaround endpoint for getting a single post by ID"""
    from models.post import Post
    from models.user import User
    
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Post not found")
    
    user = db.query(User).filter(User.id == post.user_id).first()
    
    return {
        "id": post.id,
        "user_id": post.user_id,
        "username": user.username if user else None,
        "user_full_name": user.full_name if user else None,
        "image_url": post.image_url,
        "title": post.title,
        "caption": post.caption,
        "tags": post.tags,
        "views": post.views or 0,
        "downloads": post.downloads or 0,
        "created_at": post.created_at.isoformat(),
        "updated_at": post.updated_at.isoformat()
    }

@app.get("/api/posts")
def get_posts_workaround(db: Session = Depends(get_db)):
    """Temporary workaround endpoint for getting posts"""
    from models.post import Post
    from models.user import User
    
    posts = db.query(Post).order_by(Post.created_at.desc()).limit(20).all()
    result = []
    
    for post in posts:
        user = db.query(User).filter(User.id == post.user_id).first()
        result.append({
            "id": post.id,
            "user_id": post.user_id,
            "username": user.username if user else None,
            "user_full_name": user.full_name if user else None,
            "image_url": post.image_url,
            "title": post.title,
            "caption": post.caption,
            "tags": post.tags,
            "views": post.views or 0,
            "downloads": post.downloads or 0,
            "created_at": post.created_at.isoformat(),
            "updated_at": post.updated_at.isoformat()
        })
    
    return result

@app.get("/api/posts/user/{user_id}")
def get_user_posts_workaround(user_id: int, db: Session = Depends(get_db)):
    """Temporary workaround endpoint for getting user posts"""
    from models.post import Post
    from models.user import User
    
    posts = db.query(Post).filter(Post.user_id == user_id).order_by(Post.created_at.desc()).all()
    result = []
    
    for post in posts:
        user = db.query(User).filter(User.id == post.user_id).first()
        result.append({
            "id": post.id,
            "user_id": post.user_id,
            "username": user.username if user else None,
            "user_full_name": user.full_name if user else None,
            "image_url": post.image_url,
            "title": post.title,
            "caption": post.caption,
            "tags": post.tags,
            "views": post.views or 0,
            "downloads": post.downloads or 0,
            "created_at": post.created_at.isoformat(),
            "updated_at": post.updated_at.isoformat()
        })
    
    return result

@app.post("/api/posts/{post_id}/view")
def track_view_workaround(post_id: int, db: Session = Depends(get_db)):
    """Track a view for a post"""
    from models.post import Post
    from fastapi import HTTPException
    
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    post.views = (post.views or 0) + 1
    db.commit()
    db.refresh(post)
    
    return {"views": post.views}

@app.post("/api/posts/{post_id}/download")
def track_download_workaround(post_id: int, db: Session = Depends(get_db)):
    """Track a download for a post"""
    from models.post import Post
    from fastapi import HTTPException
    
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    post.downloads = (post.downloads or 0) + 1
    db.commit()
    db.refresh(post)
    
    return {"downloads": post.downloads}

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
