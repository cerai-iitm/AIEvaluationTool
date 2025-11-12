from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from database import get_db, get_current_user
from models import user as user_model
from controllers import users as users_controller
from schemas import UserCreate, UserOut, UserActivityCreate, UserActivityResponse


users_router = APIRouter(prefix="/api/users")


@users_router.get("/me", response_model=UserOut)
async def get_current_user_info(current_user: user_model.Users = Depends(get_current_user)):
    """Get current authenticated user information."""
    return UserOut(
        user_name=current_user.user_name,
        email=current_user.email,
        role=str(current_user.role)
    )


@users_router.get("", response_model=List[UserOut])
async def get_users(db: Session = Depends(get_db)):
    rows = users_controller.list_users(db)
    # Map ORM to response schema
    return [
        UserOut(user_name=row.user_name, email=row.email, role=str(row.role))
        for row in rows
    ]


@users_router.post("", response_model=UserOut)
async def create_user(payload: UserCreate, db: Session = Depends(get_db)):
    user = users_controller.create_user(db, payload)
    return UserOut(user_name=user.user_name, email=user.email, role=str(user.role))


@users_router.get("/activity/{entity_type}", response_model=List[UserActivityResponse])
async def get_activity_by_entity_type(entity_type: str, db: Session = Depends(get_db)):
    """Get activity logs for a specific entity type (e.g., 'Test Case', 'Target', 'Domain')."""
    rows = users_controller.list_activity_by_entity_type(db, entity_type)
    def map_status(op: str) -> str:
        title = str(op).capitalize()
        if title == 'Create':
            return 'Created'
        if title == 'Update':
            return 'Updated'
        if title == 'Delete':
            return 'Deleted'
        return title

    return [
        UserActivityResponse(
            user_name=row.user_name,
            description=row.note,
            type=row.entity_type,
            testCaseId=row.entity_id,
            status=map_status(row.operation),
            timestamp=row.created_at.strftime("%Y-%m-%d %H:%M"),
        )
        for row in rows
    ]


@users_router.get("/{username}", response_model=List[UserActivityResponse])
async def get_user_activity(username: str, db: Session = Depends(get_db)):
    rows = users_controller.list_user_activity(db, username)
    def map_status(op: str) -> str:
        title = str(op).capitalize()
        if title == 'Create':
            return 'Created'
        if title == 'Update':
            return 'Updated'
        if title == 'Delete':
            return 'Deleted'
        return title

    return [
        UserActivityResponse(
            user_name=row.user_name,
            description=row.note,
            type=row.entity_type,
            testCaseId=row.entity_id,
            status=map_status(row.operation),
            timestamp=row.created_at.strftime("%Y-%m-%d %H:%M"),
        )
        for row in rows
    ]


# @users_router.post("/{username}/activity", response_model=UserActivityResponse)
# async def add_user_activity(username: str, payload: UserActivityCreate, db: Session = Depends(get_db)):
#     row = users_controller.add_user_activity(db, username, payload)
#     status_map = {
#         'create': 'Created',
#         'update': 'Updated',
#         'delete': 'Deleted',
#     }
#     return UserActivityResponse(
#         description=row.note,
#         type=row.entity_type,
#         testCaseId=row.entity_id,
#         status=status_map.get(str(row.operation), str(row.operation)),
#         timestamp=row.created_at.strftime("%Y-%m-%d %H:%M"),
#     )


