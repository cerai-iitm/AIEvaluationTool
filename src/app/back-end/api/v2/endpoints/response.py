from typing import List, Optional

from config.settings import settings
from database.fastapi_deps import _get_db
from fastapi import APIRouter, Depends, Header, HTTPException, status
from jose import JWTError, jwt
from schemas.response import (
    ResponseCreateV2,
    ResponseDetailResponse,
    ResponseListResponse,
    ResponseUpdateV2,
)
from sqlalchemy.exc import IntegrityError
from utils.activity_logger import log_activity

from lib.orm.DB import DB
from lib.orm.tables import Responses
from lib.data import Response, Prompt

response_router = APIRouter(prefix="/api/v2/responses")


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


@response_router.get(
    "",
    response_model=List[ResponseListResponse],
    summary="List all responses (v2)",
)
def list_responses(db: DB = Depends(_get_db)):
    responses = db.responses 

    return [
        ResponseListResponse(
            response_id=response.response_id,
            response_text=response.response_text,
        )
        for response in responses
    ]


# @response_router.get(
#     "",
#     response_model=List[ResponseListResponse],
#     summary="List all responses (v2)",
# )
# def list_responses(db: DB = Depends(_get_db)):
#     return db.list_responses_with_metadata() or []


@response_router.get(
    "/{response_id}",
    response_model=ResponseDetailResponse,
    summary="Get a response by ID (v2)",
)
def get_response(response_id: int, db: DB = Depends(_get_db)):
    response = db.get_response(response_id)
    if response is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Response not found"
        )

    language_name = db.get_language_name(response.lang_id)
    
    if language_name is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Language not found"
        )

    prompt = db.get_prompt(response.prompt_id)
    
    if prompt is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Prompt not found"
        )

    return ResponseDetailResponse(
        response_id=response.response_id,
        response_text=response.response_text,
        response_type=response.response_type,
        language = language_name,
        user_prompt = prompt.user_prompt,
        system_prompt = prompt.system_prompt

    )


# @response_router.get(
#     "/{response_id}",
#     response_model=ResponseDetailResponse,
#     summary="Get a response by ID (v2)",
# )
# def get_response(response_id: int, db: DB = Depends(_get_db)):
#     response = db.get_response_with_metadata(response_id)
#     if response is None:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND, detail="Response not found"
#         )
#     return response

@response_router.post(
    "/create",
    response_model=ResponseDetailResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new response (v2)",
)
def create_response(
    payload: ResponseCreateV2,
    db: DB = Depends(_get_db),
    authorization: Optional[str] = Header(None),
):
    try:
        with db.Session() as session:
            existing_ids = [row[0] for row in session.query(Responses.response_id).order_by(Responses.response_id).all()]
            next_id = 1
            for id in existing_ids:
                if id != next_id:
                    break
                next_id += 1

        lang_id = db.add_or_get_language_id(payload.language)

        prompt_obj = Prompt(user_prompt=payload.user_prompt, system_prompt=payload.system_prompt, lang_id=lang_id)
        prompt_id = db.add_or_get_prompt(prompt_obj)
        
        if prompt_id == -1:
             raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to process prompt.")

        response_data = Response(response_text=payload.response_text, response_type=payload.response_type, lang_id=lang_id)
        response_obj = db._DB__add_or_get_response_by_custom_id(response_data, prompt_id, next_id)
        if response_obj is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A response with the same content already exists.",
            )

        username = _get_username_from_token(authorization)
        if username:
            log_activity(
                username=username,
                entity_type="Response",
                entity_id=str(response_obj.response_id),
                operation="create",
                note=f"Created prompt with ID:{response_obj.response_id}",
            )

        return ResponseDetailResponse(
            response_id=response_obj.response_id,
            response_text=response_obj.response_text,
            response_type=response_obj.response_type,
            language = payload.language,
            user_prompt = payload.user_prompt,
            system_prompt = payload.system_prompt
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))



# @response_router.post(
#     "/create",
#     response_model=ResponseDetailResponse,
#     status_code=status.HTTP_201_CREATED,
#     summary="Create a new response (v2)",
# )
# def create_response(
#     payload: ResponseCreateV2,
#     db: DB = Depends(_get_db),
#     authorization: Optional[str] = Header(None),
# ):
#     try:
#         response_id = db.create_response_v2(payload.model_dump())
#     except IntegrityError:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail="A response with the same content already exists.",
#         )
#     except ValueError as e:
#         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

#     created = db.get_response_with_metadata(response_id)
#     if created is None:
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail="Response created but could not be loaded.",
#         )

#     username = _get_username_from_token(authorization)
#     if username:
#         log_activity(
#             username=username,
#             entity_type="Response",
#             entity_id=str(created["response_id"]),
#             operation="create",
#             note=f"Response '{created['response_id']}' created (v2)",
#         )

#     return created


@response_router.put(
    "/update/{response_id}",
    response_model=ResponseDetailResponse,
    summary="Update a response (v2)",
)
def update_response(
    response_id: int,
    payload: ResponseUpdateV2,
    db: DB = Depends(_get_db),
    authorization: Optional[str] = Header(None),
):
    update_data = payload.model_dump(exclude_unset=True)
    if not update_data:
        existing = db.get_response_with_metadata(response_id)
        if existing is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Response not found"
            )
        return existing

    try:
        updated = db.update_response_v2(response_id, update_data)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        ) from exc

    if updated is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Response not found"
        )

    username = _get_username_from_token(authorization)
    if username:
        log_activity(
            username=username,
            entity_type="Response",
            entity_id=str(updated["response_id"]),
            operation="update",
            note="Response updated via v2 endpoint",
        )

    return updated


@response_router.delete(
    "/delete/{response_id}",
    summary="Delete a response (v2)",
)
def delete_response(
    response_id: int,
    db: DB = Depends(_get_db),
    authorization: Optional[str] = Header(None),
):
    existing = db.get_response(response_id)
    if existing is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Response not found"
        )

    if not db.delete_response_record(response_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Response not found"
        )

    username = _get_username_from_token(authorization)
    if username:
        log_activity(
            username=username,
            entity_type="Response",
            entity_id=str(existing["response_id"]),
            operation="delete",
            note=f"Response '{existing['response_id']}' deleted",
        )

    return {"message": "Response deleted successfully"}
