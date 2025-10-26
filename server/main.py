from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import text
from database import get_db, engine, Base
from routers import auth
from models import *  # Import all models
from dotenv import load_dotenv
import os
from mangum import Mangum

# Load environment variables
load_dotenv()

app = FastAPI()

# Startup event to create tables
@app.on_event("startup")
async def startup_event():
    print("Starting server...")
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    
    # Check if email column exists and add it if not
    with engine.connect() as conn:
        result = conn.execute(text(
            "SELECT column_name FROM information_schema.columns WHERE table_name='users' AND column_name='email'"
        ))
        if not result.fetchone():
            print("Adding email column to users table...")
            conn.execute(text("ALTER TABLE users ADD COLUMN email VARCHAR UNIQUE"))
            conn.commit()
            print("Email column added successfully!")
        else:
            print("Email column already exists.")
    
    print("Database tables created successfully!")
    print("Server ready to accept connections")

# CORS configuration
cors_origins = [
    "http://localhost:5173",
    "https://social.hanumantjain.tech",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include auth routes
app.include_router(auth.router, prefix="/auth", tags=["authentication"])

@app.get("/")
def read_root():
    return {"message": "Hello from FastAPI"}

@app.get("/health")
def health_check(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        return {"status": "Database connection successful"}
    except Exception as e:
        return {"status": "Database connection failed", "error": str(e)}

handler = Mangum(app)