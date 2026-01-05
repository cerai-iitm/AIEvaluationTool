from typing import List, Optional

from config.settings import settings
from database.fastapi_deps import _get_db
from fastapi import APIRouter, Depends, Header, HTTPException, status
from jose import JWTError, jwt
from schemas.target import (
    TargetCreateV2,
    TargetDetailResponse,
    TargetListResponse,
    TargetUpdateV2,
)
from sqlalchemy.exc import IntegrityError
from utils.activity_logger import log_activity

from lib.orm.DB import DB
from lib.orm.tables import Targets
from sqlalchemy.orm import joinedload
from enum import Enum

target_router = APIRouter(prefix="/api/v2/targets")

class TargetTypeEnum(str, Enum):
    WhatsApp = "WhatsApp"
    WebApp = "WebApp"
    API = "API"

@target_router.get("/target/types", response_model=list[TargetTypeEnum], summary="Get all target types")
def get_target_types(db: DB = Depends(_get_db)):
    return list(TargetTypeEnum) 


def _get_username_from_token(authorization: Optional[str]) -> Optional[str]:
    if not authorization:
        return None
    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            return None
    except ValueError:
        return None

    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )
        return payload.get("user_name")
    except JWTError:
        return None


@target_router.get(
    "",
    response_model=List[TargetDetailResponse],
    summary="List all targets (v2)",
)
def list_targets(db: DB = Depends(_get_db)):
    
    targets = db.targets

    return [
        TargetDetailResponse(
            target_id=target.target_id,
            target_name=target.target_name,
            target_type=target.target_type,
            target_description= target.target_description,
            target_url=target.target_url,
            domain_name=target.target_domain,
            lang_list=[lang for lang in target.target_languages],
        )
        for target in targets
    ]



# @target_router.get(
#     "",
#     response_model=List[TargetListResponse],
#     summary="List all targets (v2)",
# )
# def list_targets(db: DB = Depends(_get_db)):
#     return db.list_targets_with_metadata() or []


@target_router.get(
    "/{target_id}",
    response_model=TargetDetailResponse,
    summary="Get a target by ID (v2)",
)
def get_target(target_id: int, db: DB = Depends(_get_db)):
    target = db.get_target_by_id(target_id)
    if target is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Target not found"
        )
    return TargetDetailResponse(
        target_id=target.target_id,
        target_name=target.target_name,
        target_type=target.target_type,
        target_description= target.target_description,
        target_url=target.target_url,
        domain_name=target.target_domain,
        lang_list=[lang for lang in target.target_languages],
    )



# @target_router.get(
#     "/{target_id}",
#     response_model=TargetDetailResponse,
#     summary="Get a target by ID (v2)",
# )
# def get_target(target_id: int, db: DB = Depends(_get_db)):
#     target = db.get_target_with_metadata(target_id)
#     if target is None:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND, detail="Target not found"
#         )
#     return target


@target_router.post(
    "/create",
    response_model=TargetDetailResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new target (v2)",
)
def create_target(
    payload: TargetCreateV2,
    db: DB = Depends(_get_db),
    authorization: Optional[str] = Header(None),
):
    #try: 
    with db.Session() as session:
        try:
        # Get next available ID
            existing_ids = [row[0] for row in session.query(Targets.target_id).order_by(Targets.target_id).all()]
            next_id = 1
            for id in existing_ids:
                if id != next_id:
                    break
                next_id += 1
                
            # Get or create domain
            domain_id = db.add_or_get_domain_id(payload.domain_name)
            
            # Create target
            target_obj = db._DB__add_or_get_target_custom_id(payload, next_id, domain_id)
            if target_obj is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="A target with the same name already exists.",
                )
            
            # Log activity
            username = _get_username_from_token(authorization)
            if username:
                log_activity(
                    username=username,
                    entity_type="Target",
                    entity_id=str(target_obj.target_id),
                    operation="create",
                    note=f"Target - {target_obj.target_name} created",
                    user_note=payload.notes,
                )
            
            # Create response
            return TargetDetailResponse(
                target_id=target_obj.target_id,
                target_name=target_obj.target_name,
                target_type=target_obj.target_type,
                target_description=target_obj.target_description,
                target_url=target_obj.target_url,
                domain_name=payload.domain_name,
                lang_list=payload.target_languages,
            )
            
        except IntegrityError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A target with the same name already exists.",
            )
        
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e),
            )
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"An unexpected error occurred: {str(e)}",
            )




# @target_router.post(
#     "/create",
#     response_model=TargetDetailResponse,
#     status_code=status.HTTP_201_CREATED,
#     summary="Create a new target (v2)",
# )
# def create_target(
#     payload: TargetCreateV2,
#     db: DB = Depends(_get_db),
#     authorization: Optional[str] = Header(None),
# ):
#     try:
#         target_id = db.create_target_v2(payload.model_dump())
#     except IntegrityError:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail="A target with the same name already exists.",
#         )
#     except ValueError as e:
#         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

#     created = db.get_target_with_metadata(target_id)
#     if created is None:
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail="Target created but could not be loaded.",
#         )

#     username = _get_username_from_token(authorization)
#     if username:
#         log_activity(
#             username=username,
#             entity_type="Target",
#             entity_id=str(created["target_name"]),
#             operation="create",
#             note=f"Target '{created['target_name']}' created (v2)",
#         )

#     return created


@target_router.put(
    "/update/{target_id}",
    response_model=TargetDetailResponse,
    summary="Update a target (v2)",
)
def update_target(
    target_id: int,
    payload: TargetUpdateV2,
    db: DB = Depends(_get_db),
    authorization: Optional[str] = Header(None),
):
    update_data = payload.model_dump(exclude_unset=True)
    # if not update_data:
    #     existing = db.get_target_by_id(target_id)
    #     if existing is None:
    #         raise HTTPException(
    #             status_code=status.HTTP_404_NOT_FOUND, detail="Target not found"
    #         )
    #     return existing

    try:
        existing = db.get_target_by_id(target_id)
        if existing is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Target not found"
            )

        original_name = existing.target_name
        original_type = existing.target_type
        original_description = existing.target_description
        original_url = existing.target_url
        original_domain_name = existing.target_domain if hasattr(existing, "target_domain") else None
        original_lang_names = sorted(existing.target_languages) if hasattr(existing, "target_languages") and existing.target_languages else []


        updated = db.update_target_by_id(target_id, update_data)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        ) from exc

    if updated is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Target not found"
        )

    username = _get_username_from_token(authorization)
    if not username:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")

    changes = []

    if payload.target_name and original_name != payload.target_name:
        changes.append(f"Name changed from '{original_name}' to '{payload.target_name}'")
    if payload.target_type and original_type != payload.target_type:
        changes.append("Type changed")
    if payload.target_description and original_description != payload.target_description:
        changes.append("Description changed")
    if payload.target_url and original_url != payload.target_url:
        changes.append("URL changed")
    if payload.domain_name and original_domain_name != payload.domain_name:
        changes.append("Domain changed")
    if payload.lang_list is not None:
        updated_lang_names = sorted(payload.lang_list)
        if original_lang_names != updated_lang_names:
            changes.append("Languages changed")

    note = f"Target - {updated.target_name} updated"
    if changes:
        note += f" : {', '.join(changes)}"
    else:
        note += " (no changes detected)"
    

    log_activity(
        username=username,
        entity_type="Target",
        entity_id=str(updated.target_id),
        operation="update",
        note=note,
        user_note=payload.notes,
    )

    return TargetDetailResponse(
        target_id=updated.target_id,
        target_name=updated.target_name,
        target_type=updated.target_type,
        target_description=updated.target_description,
        target_url=updated.target_url,
        domain_name=getattr(updated, "target_domain", None),
        lang_list=getattr(updated, "target_languages", []),
    )


@target_router.delete(
    "/delete/{target_id}",
    summary="Delete a target (v2)",
)
def delete_target(
    target_id: int,
    db: DB = Depends(_get_db),
    authorization: Optional[str] = Header(None),
):
    existing = db.get_target_by_id(target_id)
    if existing is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Target not found"
        )

    if not db.delete_target_record(target_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Target not found"
        )

    username = _get_username_from_token(authorization)
    if username:
        log_activity(
            username=username,
            entity_type="Target",
            entity_id=str(existing.target_id),
            operation="delete",
            note=f"Target - {existing.target_name} deleted",
            user_note=None,
        )

    return {"message": "Target deleted successfully"}
