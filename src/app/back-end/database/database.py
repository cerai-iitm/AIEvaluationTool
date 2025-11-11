from sqlalchemy import create_engine
# from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from config import helpers
from models import user
from fastapi import Depends, HTTPException, status, Header
from jose import jwt, JWTError
from config.settings import settings
from typing import Optional


SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine( 
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    """Get current user from JWT token."""
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header missing",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    try:
        # Extract token from "Bearer <token>" format
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication scheme",
                headers={"WWW-Authenticate": "Bearer"},
            )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_name: str = payload.get("user_name")
        if user_name is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    db_user = db.query(user.Users).filter(user.Users.user_name == user_name).first()
    if db_user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return db_user

def init_db():
    # Create all tables based on the Base metadata.
    user.Base.metadata.create_all(bind=engine, checkfirst=True)

# def init_db():
#     # Create all tables based on the Base metadata.
#     from app.models.user import Users
#     Base.metadata.create_all(bind=engine, checkfirst=True)


def seed_users():
    # Local import to avoid circular imports at module import time
    # from app.models.user import Users

    db = SessionLocal()
    try:
        if not db.query(user.Users).first():
            users = [
                user.Users(user_name="admin", email="admin@example.com", password=helpers.hash_password("admin123"), role="admin", is_active=True),
                user.Users(user_name="manager", email="manager@example.com", password=helpers.hash_password("manager123"), role="manager", is_active=True),
                user.Users(user_name="curator", email="curator@example.com", password=helpers.hash_password("curator123"), role="curator", is_active=True),
                user.Users(user_name="user", email="user@example.com", password=helpers.hash_password("viewer123"), role="viewer", is_active=True),
            ]
            db.add_all(users)
            db.commit()
    finally:
        db.close()