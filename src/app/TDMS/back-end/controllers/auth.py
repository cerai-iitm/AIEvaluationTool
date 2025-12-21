from sqlalchemy.orm import Session
from models.user import Users
from schemas import Login
from config import helpers
from fastapi import HTTPException
from typing import Dict

# In-memory storage for refresh tokens (in production, use Redis or database)
# Format: {refresh_token: user_name}
refresh_token_store: Dict[str, str] = {}

def get_user_by_userID(db: Session, user_name: str):
    return db.query(Users).filter(Users.user_name == user_name).first()

def login(db: Session, user: Login):
    try:
        user_db = get_user_by_userID(db, user.user_name)
        if not user_db:
            raise HTTPException(status_code=400, detail="Invalid user name")
        
        if not helpers.verify_password(user.password, user_db.password):
            raise HTTPException(status_code=400, detail="Invalid password")

        token_data = {
            "user_name": user_db.user_name,
        }

        access_token = helpers.create_access_token(data=token_data)
        refresh_token = helpers.create_refresh_token(data=token_data)
        
        # Store refresh token
        refresh_token_store[refresh_token] = user_db.user_name

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "message": "Login successful",
            "Status": True
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


def refresh_access_token(refresh_token: str, db: Session):
    """Generate a new access token from a refresh token."""
    try:
        # Verify refresh token
        payload = helpers.verify_refresh_token(refresh_token)
        user_name = payload.get("user_name")
        
        if not user_name:
            raise HTTPException(status_code=401, detail="Invalid refresh token")
        
        # Check if refresh token is in store (optional validation)
        if refresh_token not in refresh_token_store:
            raise HTTPException(status_code=401, detail="Refresh token not found or revoked")
        
        # Verify user still exists
        user_db = get_user_by_userID(db, user_name)
        if not user_db:
            raise HTTPException(status_code=401, detail="User not found")
        
        # Generate new access token
        token_data = {
            "user_name": user_name,
        }
        new_access_token = helpers.create_access_token(data=token_data)
        
        return {
            "access_token": new_access_token,
            "message": "Token refreshed successfully",
            "Status": True
        }
        
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


def revoke_refresh_token(refresh_token: str):
    """Revoke a refresh token (logout)."""
    if refresh_token in refresh_token_store:
        del refresh_token_store[refresh_token]
        return {"message": "Token revoked successfully", "Status": True}
    return {"message": "Token not found", "Status": False}