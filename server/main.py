from fastapi import FastAPI, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session
from database import get_db, engine, Base
from routers.auth import router as auth_router
from routers.posts import router as posts_router
from middleware import RequestLoggingMiddleware
from logger import logger
from dotenv import load_dotenv
from mangum import Mangum
import os

# Load environment variables
load_dotenv()

app = FastAPI(
    title="Social Hub API",
    description="API for Social Hub application",
    version="1.0.0"
)

@app.on_event("startup")
async def startup_event():
    """Run migrations and initialize database on startup"""
    logger.info("Initializing FastAPI application")
    
    # Run database migrations
    logger.info("Running database migrations...")
    try:
        from migrations.migrate import run_migrations
        run_migrations()
    except Exception as e:
        logger.error(f"Migration error: {str(e)}")
        # Continue anyway - migrations might have failed but app can still start
    
    # Create tables (for new deployments)
    logger.info("Creating database tables...")
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database initialization complete!")
    except Exception as e:
        logger.error(f"Table creation error: {str(e)}")
        # Continue anyway - tables might already exist

# Add Request Logging Middleware (should be first)
app.add_middleware(RequestLoggingMiddleware)

# CORS configuration - get from environment variables
cors_origins_env = os.getenv("CORS_ORIGINS", "")
cors_origins = [origin.strip() for origin in cors_origins_env.split(",") if origin.strip()] if cors_origins_env else [
    "https://galleryai.hanumantjain.tech",
]

# Log CORS configuration
logger.info(f"CORS origins configured: {cors_origins}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=3600,
)

# Helper function to add CORS headers to any response
def add_cors_headers(response, origin: str = None):
    """Add CORS headers to response"""
    # Check if origin is allowed (case-insensitive check)
    origin_lower = origin.lower() if origin else ""
    allowed_origin = None
    
    for allowed in cors_origins:
        if allowed.lower() == origin_lower:
            allowed_origin = allowed
            break
    
    # Set the origin (use first allowed if no match, or use wildcard if credentials not needed)
    if allowed_origin:
        response.headers["Access-Control-Allow-Origin"] = allowed_origin
    elif cors_origins:
        response.headers["Access-Control-Allow-Origin"] = cors_origins[0]
    
    response.headers["Access-Control-Allow-Credentials"] = "true"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS, PATCH"
    response.headers["Access-Control-Allow-Headers"] = "*"
    response.headers["Access-Control-Max-Age"] = "3600"
    return response

# Exception handlers to ensure CORS headers are included in error responses
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Handle HTTP exceptions with CORS headers"""
    origin = request.headers.get("origin", "")
    response = JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )
    return add_cors_headers(response, origin)

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors with CORS headers"""
    origin = request.headers.get("origin", "")
    response = JSONResponse(
        status_code=422,
        content={"detail": exc.errors()}
    )
    return add_cors_headers(response, origin)

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle all other exceptions with CORS headers"""
    origin = request.headers.get("origin", "")
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    response = JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )
    return add_cors_headers(response, origin)

# Add middleware to ensure CORS headers on all responses (must be after CORS middleware)
@app.middleware("http")
async def ensure_cors_headers(request: Request, call_next):
    """Ensure CORS headers are added to all responses, including redirects"""
    # Handle OPTIONS preflight requests directly
    if request.method == "OPTIONS":
        origin = request.headers.get("origin", "")
        response = JSONResponse(content={}, status_code=200)
        return add_cors_headers(response, origin)
    
    response = await call_next(request)
    
    # Get origin from request
    origin = request.headers.get("origin", "")
    
    # Add CORS headers if not already present (handles redirects and all responses)
    if "Access-Control-Allow-Origin" not in response.headers:
        add_cors_headers(response, origin)
    
    return response

# Routers
app.include_router(auth_router, prefix="/auth", tags=["authentication"])
app.include_router(posts_router, prefix="/api/posts", tags=["posts"])

@app.get("/")
def read_root():
    """Root endpoint"""
    return {"message": "Social Hub API", "version": "1.0.0"}

@app.get("/health")
def health_check(db: Session = Depends(get_db)):
    """Health check endpoint"""
    try:
        db.execute(text("SELECT 1"))
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return {"status": "unhealthy", "database": "disconnected", "error": str(e)}

# Lambda handler
handler = Mangum(app, lifespan="off")
