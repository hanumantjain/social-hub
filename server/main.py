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

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Exception handlers to ensure CORS headers are included in error responses
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Handle HTTP exceptions with CORS headers"""
    origin = request.headers.get("origin", "")
    response = JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )
    if origin in cors_origins:
        response.headers["Access-Control-Allow-Origin"] = origin
    else:
        response.headers["Access-Control-Allow-Origin"] = cors_origins[0]
    response.headers["Access-Control-Allow-Credentials"] = "true"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS, PATCH"
    response.headers["Access-Control-Allow-Headers"] = "*"
    return response

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors with CORS headers"""
    origin = request.headers.get("origin", "")
    response = JSONResponse(
        status_code=422,
        content={"detail": exc.errors()}
    )
    if origin in cors_origins:
        response.headers["Access-Control-Allow-Origin"] = origin
    else:
        response.headers["Access-Control-Allow-Origin"] = cors_origins[0]
    response.headers["Access-Control-Allow-Credentials"] = "true"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS, PATCH"
    response.headers["Access-Control-Allow-Headers"] = "*"
    return response

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle all other exceptions with CORS headers"""
    origin = request.headers.get("origin", "")
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    response = JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )
    if origin in cors_origins:
        response.headers["Access-Control-Allow-Origin"] = origin
    else:
        response.headers["Access-Control-Allow-Origin"] = cors_origins[0]
    response.headers["Access-Control-Allow-Credentials"] = "true"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS, PATCH"
    response.headers["Access-Control-Allow-Headers"] = "*"
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
