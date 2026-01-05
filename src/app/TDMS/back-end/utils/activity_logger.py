"""Utility functions for logging user activities."""
from sqlalchemy.orm import Session
from database.database import SessionLocal
from models.user import ActivityLog, Users
from fastapi import HTTPException
from typing import Optional


def log_activity(
    username: str,
    entity_type: str,
    entity_id: str,
    operation: str,
    note: str,
    user_note: Optional[str] = None
) -> Optional[ActivityLog]:
    """
    Log an activity to the ActivityLog table.
    
    Args:
        username: The username of the user performing the action
        entity_type: Type of entity (e.g., "Test Case", "Target", "Domain")
        entity_id: ID of the entity (as string)
        operation: Type of operation ("create", "update", "delete")
        note: Description of what was done (system-generated)
        user_note: Optional user-entered notes
    
    Returns:
        ActivityLog object if successful, None if user not found
    """
    db: Session = SessionLocal()
    try:
        # Get user to get their role
        user = db.query(Users).filter(Users.user_name == username).first()
        if not user:
            # User not found - return None instead of raising exception
            # This allows the main operation to continue even if logging fails
            return None
        
        activity = ActivityLog(
            user_name=username,
            role=user.role,
            entity_type=entity_type,
            entity_id=str(entity_id),
            note=note,
            user_note=user_note or "",
            operation=operation.lower(),
        )
        db.add(activity)
        db.commit()
        db.refresh(activity)
        return activity
    except Exception as e:
        # Log the error but don't fail the main operation
        db.rollback()
        print(f"Error logging activity: {e}")
        return None
    finally:
        db.close()

