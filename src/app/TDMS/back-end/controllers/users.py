from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text
from fastapi import HTTPException

from models.user import Users, ActivityLog
from schemas import UserCreate, UserActivityCreate, UpdateUser
from config import helpers

_OP_ALIASES = {
    "created": "create",
    "updated": "update",
    "deleted": "delete",
}


def _normalize_operation(op: str) -> str:
    value = (op or "").strip().lower()
    return _OP_ALIASES.get(value, value)


def _normalize_legacy_activity_operations(db: Session) -> None:
    updates = [
        ("created", "create"),
        ("updated", "update"),
        ("deleted", "delete"),
    ]
    changed = False
    for legacy, current in updates:
        result = db.execute(
            text('UPDATE "ActivityLog" SET operation = :current WHERE lower(operation) = :legacy'),
            {"current": current, "legacy": legacy},
        )
        changed = changed or (result.rowcount or 0) > 0
    if changed:
        db.commit()


def list_users(db: Session) -> List[Users]:
    return db.query(Users).all()


def _add_activity_for_actor(
    db: Session,
    actor: Users,
    entity_type: str,
    entity_id: str,
    operation: str,
    note: str,
) -> ActivityLog:
    activity = ActivityLog(
        user_name=actor.user_name,
        role=actor.role,
        entity_type=entity_type,
        entity_id=str(entity_id),
        note=note,
        user_note="",
        operation=_normalize_operation(operation),
    )
    db.add(activity)
    return activity


def create_user(db: Session, payload: UserCreate, actor: Optional[Users] = None) -> Users:
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
    db.flush()

    if actor:
        _add_activity_for_actor(
            db=db,
            actor=actor,
            entity_type="User",
            entity_id=user.user_id,
            operation="create",
            note=f"User - {user.user_name} created with role {user.role}",
        )

    db.commit()
    db.refresh(user)
    return user

def delete_user(db: Session, user_id: str, actor: Optional[Users] = None) -> Users:
    user = db.query(Users).filter(Users.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if actor:
        _add_activity_for_actor(
            db=db,
            actor=actor,
            entity_type="User",
            entity_id=user.user_id,
            operation="delete",
            note=f"User - {user.user_name} deleted",
        )

    db.delete(user)
    db.commit()
    return user

def update_user(db:Session, user_id: str, payload: UpdateUser, actor: Optional[Users] = None) -> Users:
    user = db.query(Users).filter(Users.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    original_user_name = user.user_name
    original_email = user.email
    original_role = str(user.role)
    original_is_active = user.is_active

    user.user_name = payload.user_name
    user.email = payload.email
    user.role = payload.role.lower()
    if payload.password:
        user.password = helpers.hash_password(payload.password)
    if payload.is_active is not None:
        user.is_active = payload.is_active

    if actor:
        changes = []
        if original_user_name != user.user_name:
            changes.append(f"name changed from {original_user_name} to {user.user_name}")
        if original_email != user.email:
            changes.append("email changed")
        if original_role != str(user.role):
            changes.append(f"role changed from {original_role} to {user.role}")
        if original_is_active != user.is_active:
            changes.append(f"active status changed to {user.is_active}")
        if payload.password:
            changes.append("password changed")

        note = f"User - {user.user_name} updated"
        if changes:
            note += f" : {', '.join(changes)}"

        _add_activity_for_actor(
            db=db,
            actor=actor,
            entity_type="User",
            entity_id=user.user_id,
            operation="update",
            note=note,
        )

    db.commit()
    db.refresh(user)
    return user


def list_user_activity(db: Session, username: str) -> List[ActivityLog]:
    _normalize_legacy_activity_operations(db)
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
        user_note="",
        operation=_normalize_operation(payload.operation),
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
        user_note="",
        operation=_normalize_operation(operation),
    )
    db.add(activity)
    db.commit()
    db.refresh(activity)
    return activity


def list_activity_by_entity_type(db: Session, entity_type: str) -> List[ActivityLog]:
    """Get activity logs filtered by entity type."""
    _normalize_legacy_activity_operations(db)
    return (
        db.query(ActivityLog)
        .filter(ActivityLog.entity_type == entity_type)
        .order_by(ActivityLog.created_at.desc())
        .all()
    )


def delete_user_activity(db: Session, user_id: str) -> None:
    # First get the user by user_id to get the username
    user = db.query(Users).filter(Users.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Delete all activities for this user by username
    activities = db.query(ActivityLog).filter(ActivityLog.user_name == user.user_name).all()
    for activity in activities:
        db.delete(activity)
    db.commit()
