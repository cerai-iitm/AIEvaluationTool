from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from controllers import auth
from database import get_db
from schemas import Login, RefreshToken

auth_router = APIRouter()

@auth_router.post("/login")
async def login(user: Login, db: Session = Depends(get_db)):
    return auth.login(db, user)


@auth_router.post("/refresh")
async def refresh_token(token_data: RefreshToken, db: Session = Depends(get_db)):
    """Refresh access token using refresh token."""
    return auth.refresh_access_token(token_data.refresh_token, db)


@auth_router.post("/logout")
async def logout(token_data: RefreshToken):
    """Revoke refresh token (logout)."""
    return auth.revoke_refresh_token(token_data.refresh_token)
