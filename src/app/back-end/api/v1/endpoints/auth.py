from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from controllers import auth
from database import get_db
from schemas import Login

auth_router = APIRouter()

@auth_router.post("/login")
async def login(user: Login, db: Session = Depends(get_db)):
    return auth.login(db, user)
