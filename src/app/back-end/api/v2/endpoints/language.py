from typing import List, Optional

from config.settings import settings
from database.fastapi_deps import _get_db
from fastapi import APIRouter, Depends, Header, HTTPException, status
from jose import JWTError, jwt
from schemas.language import (
    LanguageCreateV2,
    LanguageDetailResponse,
    LanguageListResponse,
    LanguageUpdateV2,
    Language_v2,
    LanguageBase,
)
from sqlalchemy.exc import IntegrityError
from utils.activity_logger import log_activity

from lib.orm.DB import DB
from lib.orm.tables import Languages

language_router = APIRouter(prefix="/api/v2/languages")


def _get_username_from_token(authorization: Optional[str] = Header(None)) -> Optional[str]:
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


@language_router.get(
    "",
    response_model=List[LanguageListResponse],
    summary="List all languages (v2)",
)
def list_languages(db: DB = Depends(_get_db)):
    try:
        languages = db.languages or []
        return [
            LanguageListResponse(
                lang_id=lang.code,
                lang_name=lang.name,
            )
            for lang in languages
        ]
    except Exception as e:
        db.logger.error(f"Failed to fetch languages: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error fetching languages"
        )  


# @language_router.get(
#     "",
#     response_model=List[LanguageListResponse],
#     summary="List all languages (v2)",
# )
# def list_languages(db: DB = Depends(_get_db)):
#     return db.list_languages_with_metadata() or []

@language_router.get(
    "/{lang_id}",
    response_model=LanguageDetailResponse,
    summary="Get a language by ID (v2)",
)
def get_language(lang_id: int, db: DB = Depends(_get_db)):
    lang_name = db.get_language_name(lang_id)
    if lang_name is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Language with ID {lang_id} not found",
        )
    return LanguageDetailResponse(lang_id=lang_id, lang_name=lang_name)



# @language_router.get(
#     "/{lang_id}",
#     response_model=LanguageDetailResponse,
#     summary="Get a language by ID (v2)",
# )
# def get_language(lang_id: int, db: DB = Depends(_get_db)):
#     language = db.get_language_with_metadata(lang_id)
#     if language is None:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND, detail="Language not found"
#         )
#     return language


@language_router.post(
    "/create_DB.py",
    response_model=LanguageDetailResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new language (based on DB.py)",
    
)
def create_language_v2(
    language: LanguageBase, 
    db: DB = Depends(_get_db), 
    authorization: Optional[str ]= Header(None)
):
    with db.Session() as session:
        existing_ids = [row[0] for row in session.query(Languages.lang_id).order_by(Languages.lang_id).all()]
        next_id = 1
        for id in existing_ids:
            if id != next_id:
                break
            next_id += 1
        
    lang_obj = db._DB__add_or_get_language_custom_Id(language.lang_name, next_id)
    if lang_obj is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Language '{language.lang_name}' already exists or ID conflict.",
        )
    
    username = _get_username_from_token(authorization)
    if username:
        log_activity(
            username=username,
            entity_type="Language",
            entity_id=lang_obj.lang_id,
            operation="created",
            note=f"Language '{lang_obj.lang_name}' created ",
        )
    
    return LanguageDetailResponse(
        lang_id=lang_obj.lang_id,
        lang_name=lang_obj.lang_name,
    )


# @language_router.post(
#     "/create_DB.py",
#     response_model=LanguageBase,
#     status_code=status.HTTP_201_CREATED,
#     summary="Create a new language (based on DB.py)",
# )
# def create_language_v3(language: LanguageBase, db: DB = Depends(_get_db)):
#     return db.__add_or_get_language(language)

# @language_router.post(
#     "/create_v2",
#     response_model=Language_v2,
#     status_code=status.HTTP_201_CREATED,
#     summary="Create a new language (v2)",
# )
# def create_language_v2(payload: Language_v2, db: DB = Depends(_get_db)):
#     return db.create_language_v2(payload)


@language_router.post(
    "/create",
    response_model=LanguageDetailResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new language (v2)",
)
def create_language(
    payload: LanguageCreateV2,
    db: DB = Depends(_get_db),
    authorization: Optional[str] = Header(None),
):
    try:
        lang_id = db.create_language_v2(payload.model_dump())
    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A language with the same name already exists.",
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    created = db.get_language_with_metadata(lang_id)
    if created is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Language created but could not be loaded.",
        )

    username = _get_username_from_token(authorization)
    if username:
        log_activity(
            username=username,
            entity_type="Language",
            entity_id=str(created["lang_name"]),
            operation="create",
            note=f"Language '{created['lang_name']}' created (v2)",
        )

    return created


@language_router.put(
    "/update/{lang_id}",
    response_model=LanguageDetailResponse,
    summary="Update a language (v2)",
)
def update_language(
    lang_id: int,
    payload: LanguageUpdateV2,
    db: DB = Depends(_get_db),
    authorization: Optional[str] = Header(None),
):
    update_data = payload.model_dump(exclude_unset=True)
    if not update_data:
        existing = db.get_language_with_metadata(lang_id)
        if existing is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Language not found"
            )
        return existing

    try:
        updated = db.update_language_v2(lang_id, update_data)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        ) from exc

    if updated is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Language not found"
        )

    username = _get_username_from_token(authorization)
    if username:
        log_activity(
            username=username,
            entity_type="Language",
            entity_id=str(updated["lang_name"]),
            operation="update",
            note="Language updated via v2 endpoint",
        )

    return updated


@language_router.delete(
    "/delete/{lang_id}",
    summary="Delete a language (v2)",
)
def delete_language(
    lang_id: int,
    db: DB = Depends(_get_db),
    authorization: Optional[str] = Header(None),
):
    existing = db.get_language_name(lang_id)
    if existing is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Language not found"
        )

    if not db.delete_language_record(lang_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Language not found"
        )

    username = _get_username_from_token(authorization)
    if username:
        log_activity(
            username=username,
            entity_type="Language",
            entity_id=str(existing["lang_name"]),
            operation="delete",
            note=f"Language '{existing['lang_name']}' deleted (v2)",
        )

    return {"message": "Language deleted successfully"}
