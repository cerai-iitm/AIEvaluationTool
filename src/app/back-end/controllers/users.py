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
    # Get user to get their role
    user = db.query(Users).filter(Users.user_name == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    activity = ActivityLog(
        user_name=username,
        role=user.role,
        entity_type=payload.entity_type,
        entity_id=payload.entity_id,
        note=payload.note,
        operation=payload.operation.lower(),
    )
    db.add(activity)
    db.commit()
    db.refresh(activity)
    return activity


def add_activity_log(
    db: Session,
    username: str,
    entity_type: str,
    entity_id: str,
    operation: str,
    note: str
) -> ActivityLog:
    """Helper function to add activity log."""
    # Get user to get their role
    user = db.query(Users).filter(Users.user_name == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    activity = ActivityLog(
        user_name=username,
        role=user.role,
        entity_type=entity_type,
        entity_id=entity_id,
        note=note,
        operation=operation.lower(),
    )
    db.add(activity)
    db.commit()
    db.refresh(activity)
    return activity


def list_activity_by_entity_type(db: Session, entity_type: str) -> List[ActivityLog]:
    """Get activity logs filtered by entity type."""
    return (
        db.query(ActivityLog)
        .filter(ActivityLog.entity_type == entity_type)
        .order_by(ActivityLog.created_at.desc())
        .all()
    )


