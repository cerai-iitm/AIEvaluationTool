from typing import List
from sqlalchemy.orm import Session
from fastapi import HTTPException

from models.user import Users, ActivityLog
from schemas import UserCreate, UserActivityCreate
from config import helpers


def list_users(db: Session) -> List[Users]:
    return db.query(Users).all()


def create_user(db: Session, payload: UserCreate) -> Users:
    existing_user = db.query(Users).filter((Users.user_name == payload.user_name) | (Users.email == payload.email)).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="User name or email already exists")

    if payload.password != payload.confirm_password:
        raise HTTPException(status_code=400, detail="Password and confirm password do not match")

    user = Users(
        user_name=payload.user_name,
        email=payload.email,
        role=payload.role.lower(),
        password=helpers.hash_password(payload.password),
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def list_user_activity(db: Session, username: str) -> List[ActivityLog]:
    return (
        db.query(ActivityLog)
        .filter(ActivityLog.user_name == username)
        .order_by(ActivityLog.created_at.desc())
        .all()
    )


def add_user_activity(db: Session, username: str, payload: UserActivityCreate) -> ActivityLog:
    activity = ActivityLog(
        user_name=username,
        entity_type=payload.entity_type,
        entity_id=payload.entity_id,
        note=payload.note,
        operation=payload.operation.lower(),
    )
    db.add(activity)
    db.commit()
    db.refresh(activity)
    return activity


