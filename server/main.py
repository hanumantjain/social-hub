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
    # Check if origin is in allowed list (case-insensitive)
    origin_lower = (origin or "").lower().strip()
    allowed_origin = None
    
    for allowed in cors_origins:
        if allowed.lower().strip() == origin_lower:
            allowed_origin = allowed
            break
    
    # Set the origin - must match exactly or use first allowed
    if allowed_origin:
        response.headers["Access-Control-Allow-Origin"] = allowed_origin
    elif cors_origins and origin_lower:
        # If origin provided but not in list, use first allowed (strict)
        response.headers["Access-Control-Allow-Origin"] = cors_origins[0]
    elif cors_origins:
        # No origin in request, use first allowed
        response.headers["Access-Control-Allow-Origin"] = cors_origins[0]
    
    # Always set these headers
    if "Access-Control-Allow-Origin" in response.headers:
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

# Add middleware to normalize paths and ensure CORS headers (must be after CORS middleware)
@app.middleware("http")
async def normalize_path_and_cors(request: Request, call_next):
    """Normalize paths (remove trailing slashes) and ensure CORS headers on all responses"""
    # Get origin from request early
    origin = request.headers.get("origin", "")
    
    # Normalize path - remove trailing slash (except for root) by rewriting the request
    # Don't redirect, as redirects lose CORS headers. Instead, rewrite the path in the request.
    path = request.url.path
    if path != "/" and path.endswith("/"):
        # Rewrite request URL to remove trailing slash (internal rewrite, no redirect)
        normalized_path = path.rstrip("/")
        request.scope["path"] = normalized_path
        request.scope["raw_path"] = normalized_path.encode()
        path = normalized_path  # Update path for logging
    
    # Handle OPTIONS preflight requests directly
    if request.method == "OPTIONS":
        response = JSONResponse(content={}, status_code=200)
        return add_cors_headers(response, origin)
    
    # Log the path for debugging
    logger.debug(f"Request path: {path}, Origin: {origin}, Method: {request.method}")
    
    try:
        response = await call_next(request)
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}", exc_info=True)
        response = JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"}
        )
    
    # Force add CORS headers to ALL responses (even if already present, ensures they're correct)
    add_cors_headers(response, origin)
    
    # Log CORS headers for debugging
    logger.debug(f"Response status: {response.status_code}, CORS Origin: {response.headers.get('Access-Control-Allow-Origin')}")
    
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
