from sqlalchemy.orm import Session
from models.user import Users
from schemas import Login
from config import helpers
from fastapi import HTTPException

def get_user_by_userID(db: Session, user_name: str):
    return db.query(Users).filter(Users.user_name == user_name).first()

def login(db: Session, user: Login):
    try:
        user_db = get_user_by_userID(db, user.user_name)
        if not user_db:
            raise HTTPException(status_code=400, detail="Invalid user name")
        
        if not helpers.verify_password(user.password, user_db.password):
            raise HTTPException(status_code=400, detail="Invalid password")

        access_token = helpers.create_access_token(data={
            # "id" : user_db.user_id,
            "user_name": user_db.user_name,
            # "is_active": user_db.is_active,
        })

        return {"access_token": access_token, "message" : "Login successful", "Status" : True}

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))