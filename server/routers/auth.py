from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from database import get_db
from models.user import User
from schemas.auth import UserCreate, UserLogin, UserResponse, Token, TokenData, UserUpdate, GoogleOAuthRequest
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
from logger import logger
import os
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
import re
import httpx

router = APIRouter()

# Password hashing
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

# JWT settings
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

# Utility functions
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def get_user(db: Session, username: str):
    return db.query(User).filter(User.username == username).first()

def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()

def get_user_by_google_id(db: Session, google_id: str):
    return db.query(User).filter(User.google_id == google_id).first()

def generate_username_from_email(email: str, db: Session) -> str:
    """Generate a unique username from email"""
    base_username = email.split('@')[0].lower()
    base_username = re.sub(r'[^a-z0-9]', '', base_username)  # Remove special chars
    if not base_username:
        base_username = "user"
    
    username = base_username
    counter = 1
    while get_user(db, username):
        username = f"{base_username}{counter}"
        counter += 1
    
    return username

def authenticate_user(db: Session, username: str, password: str):
    user = get_user(db, username)
    if not user:
        return False
    if not verify_password(password, user.password):
        return False
    return user

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    user = get_user(db, username=token_data.username)
    if user is None:
        raise credentials_exception
    return user

# Routes
@router.post("/signup", response_model=UserResponse)
def signup(user: UserCreate, db: Session = Depends(get_db)):
    logger.info(f"Signup attempt for username: {user.username}")
    
    # Check if user already exists
    db_user = get_user(db, username=user.username)
    if db_user:
        logger.warning(f"Signup failed: Username {user.username} already exists")
        raise HTTPException(
            status_code=400,
            detail="Username already registered"
        )
    
    # Check if email already exists
    db_user_email = db.query(User).filter(User.email == user.email).first()
    if db_user_email:
        logger.warning(f"Signup failed: Email {user.email} already exists")
        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )
    
    # Create new user
    hashed_password = get_password_hash(user.password)
    db_user = User(
        full_name=user.full_name,
        username=user.username,
        email=user.email,
        password=hashed_password,
        bio=user.bio
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    logger.info(f"User created successfully: {user.username} (ID: {db_user.id})")
    return db_user

@router.post("/login", response_model=Token)
def login(user: UserLogin, db: Session = Depends(get_db)):
    logger.info(f"Login attempt for username: {user.username}")
    
    authenticated_user = authenticate_user(db, user.username, user.password)
    if not authenticated_user:
        logger.warning(f"Login failed for username: {user.username} - Invalid credentials")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": authenticated_user.username}, expires_delta=access_token_expires
    )
    
    logger.info(f"Login successful for username: {user.username}")
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/google", response_model=Token)
def google_oauth(oauth_data: GoogleOAuthRequest, db: Session = Depends(get_db)):
    """Handle Google OAuth signin/signup"""
    logger.info("Google OAuth attempt")
    
    try:
        # The token can be either an ID token or an access token
        # First, try to verify it as an ID token
        GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
        if not GOOGLE_CLIENT_ID:
            logger.error("GOOGLE_CLIENT_ID environment variable not set")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Google OAuth not configured"
            )
        
        idinfo = None
        try:
            # Try to verify as ID token
            idinfo = id_token.verify_oauth2_token(
                oauth_data.token, 
                google_requests.Request(), 
                GOOGLE_CLIENT_ID
            )
            google_id = idinfo['sub']
            email = idinfo.get('email')
            name = idinfo.get('name', '')
            picture = idinfo.get('picture', '')
        except ValueError:
            # If ID token verification fails, try as access token
            logger.info("Token is not an ID token, trying as access token")
            with httpx.Client() as client:
                userinfo_response = client.get(
                    'https://www.googleapis.com/oauth2/v3/userinfo',
                    headers={'Authorization': f'Bearer {oauth_data.token}'}
                )
                
                if userinfo_response.status_code != 200:
                    logger.warning(f"Failed to get user info: {userinfo_response.status_code}")
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Invalid Google access token"
                    )
                
                userinfo = userinfo_response.json()
                google_id = userinfo.get('sub')
                email = userinfo.get('email')
                name = userinfo.get('name', '')
                picture = userinfo.get('picture', '')
        
        if not email:
            logger.warning("Google OAuth: No email in response")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email not provided by Google"
            )
        
        # Check if user exists by Google ID
        user = get_user_by_google_id(db, google_id)
        
        if user:
            # User exists, log them in
            logger.info(f"Google OAuth: Existing user logged in - {user.username}")
        else:
            # Check if user exists by email (for account linking scenario)
            existing_user = get_user_by_email(db, email)
            
            if existing_user:
                # Link Google account to existing user
                if existing_user.google_id:
                    logger.warning(f"Google OAuth: Email {email} already linked to another Google account")
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Email already registered with a different Google account"
                    )
                
                existing_user.google_id = google_id
                # Update name if not set or different
                if not existing_user.full_name or existing_user.full_name != name:
                    existing_user.full_name = name
                user = existing_user
                db.commit()
                db.refresh(user)
                logger.info(f"Google OAuth: Linked Google account to existing user - {user.username}")
            else:
                # Create new user
                username = generate_username_from_email(email, db)
                user = User(
                    google_id=google_id,
                    email=email,
                    full_name=name,
                    username=username,
                    password=None,  # OAuth users don't have passwords
                    bio=None
                )
                db.add(user)
                db.commit()
                db.refresh(user)
                logger.info(f"Google OAuth: New user created - {user.username} (ID: {user.id})")
        
        # Generate JWT token
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.username}, expires_delta=access_token_expires
        )
        
        return {"access_token": access_token, "token_type": "bearer"}
        
    except ValueError as e:
        # Invalid token
        logger.warning(f"Google OAuth: Invalid token - {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Google token"
        )
    except Exception as e:
        logger.error(f"Google OAuth error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="OAuth authentication failed"
        )

@router.get("/me", response_model=UserResponse)
def read_users_me(current_user: User = Depends(get_current_user)):
    logger.info(f"User profile accessed: {current_user.username}")
    return current_user

@router.patch("/me", response_model=UserResponse)
def update_user_profile(
    profile_data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    logger.info(f"Profile update attempt for user: {current_user.username}")
    
    # Update only provided fields
    if profile_data.full_name is not None:
        current_user.full_name = profile_data.full_name
        logger.info(f"Updated full_name for {current_user.username}")
    
    if profile_data.username is not None:
        # Check if username is already taken by another user
        existing_user = db.query(User).filter(
            User.username == profile_data.username,
            User.id != current_user.id
        ).first()
        if existing_user:
            logger.warning(f"Profile update failed: Username {profile_data.username} already taken")
            raise HTTPException(
                status_code=400,
                detail="Username already taken"
            )
        current_user.username = profile_data.username
        logger.info(f"Updated username to {profile_data.username}")
    
    if profile_data.bio is not None:
        current_user.bio = profile_data.bio
        logger.info(f"Updated bio for {current_user.username}")
    
    if profile_data.email is not None:
        # Check if email is already taken by another user
        existing_user = db.query(User).filter(
            User.email == profile_data.email,
            User.id != current_user.id
        ).first()
        if existing_user:
            logger.warning(f"Profile update failed: Email {profile_data.email} already taken")
            raise HTTPException(
                status_code=400,
                detail="Email already taken"
            )
        current_user.email = profile_data.email
        logger.info(f"Updated email for {current_user.username}")
    
    # Update the updated_at timestamp
    current_user.updated_at = datetime.now()
    
    db.commit()
    db.refresh(current_user)
    
    logger.info(f"Profile updated successfully for user: {current_user.username}")
    return current_user
