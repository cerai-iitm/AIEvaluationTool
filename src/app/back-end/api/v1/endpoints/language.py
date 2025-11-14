from fastapi import APIRouter, HTTPException, Depends, Header, Response
from schemas import Language, LanguageCreate, LanguageUpdate, LanguageDelete
from database.fastapi_deps import _get_db
from database.database import get_current_user
from models import user as user_model
from utils.activity_logger import log_activity
from jose import jwt, JWTError
from config.settings import settings
from typing import Optional
import os
import sys
import hashlib

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../../")))

from lib.orm.DB import DB
from lib.orm.tables import Languages

language_router = APIRouter(prefix="/api/languages")

def get_username_from_token(authorization: Optional[str] = Header(None)) -> Optional[str]:
    if not authorization:
        return None
    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            return None
    except ValueError:
        return None

    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload.get("user_name")
    except JWTError:
        return None


@language_router.get("", response_model=list[Language], summary="Get all languages")
async def list_languages(db: DB = Depends(_get_db)):
    session = db.Session()
    try:
        languages = session.query(Languages).all()
        return [
            Language(
                lang_id=lang.lang_id,
                lang_name=lang.lang_name
            )
            for lang in languages
        ]
    finally:
        session.close()


@language_router.get("/{lang_id}", response_model=Language, summary="Get a language by ID")
async def get_language(lang_id: int, db: DB = Depends(_get_db)):
    session = db.Session()
    try:
        language = session.query(Languages).filter(Languages.lang_id == lang_id).first()
        if language is None:
            raise HTTPException(status_code=404, detail="Language not found")
        return Language(
            lang_id=language.lang_id,
            lang_name=language.lang_name
        )
    finally:
        session.close()


@language_router.post("/create", response_model=Language, summary="Create a new language")
async def create_language(
        language: LanguageCreate, 
        db: DB = Depends(_get_db), 
        authorization: Optional[str] = Header(None)
    ):
    session = db.Session()
    try:
        existing_language = session.query(Languages).filter(Languages.lang_name == language.lang_name).first()
        if existing_language:
            raise HTTPException(status_code=400, detail="Language already exists")

        # Find the lowest unused lang_id
        existing_ids = [row[0] for row in session.query(Languages.lang_id).order_by(Languages.lang_id).all()]
        next_id = 1
        for id in existing_ids:
            if id != next_id:
                break
            next_id += 1

        new_language = Languages(
            lang_id=next_id,
            lang_name=language.lang_name
        )
         
        session.add(new_language)
        session.commit()
        session.refresh(new_language)

        username = get_username_from_token(authorization)
        if username:
            log_activity(
                username=username,
                entity_type="Language",
                entity_id=new_language.lang_id,
                operation="create",
                note=f"Language '{new_language.lang_name}' created"
            )

        return Language(
            lang_id=new_language.lang_id,
            lang_name=new_language.lang_name
        )
    finally:
        session.close()


@language_router.put("/update/{lang_id}", response_model=Language, summary="Update a language by ID")
async def update_language(
        lang_id: int, 
        language: LanguageUpdate, 
        db: DB = Depends(_get_db),
        authorization: Optional[str] = Header(None)
    ):
    session = db.Session()
    try:
        language_to_update = session.query(Languages).filter(Languages.lang_id == lang_id).first()
        if language_to_update is None:
            raise HTTPException(status_code=404, detail="Language not found")

        original_name = language_to_update.lang_name

        if language_to_update.lang_name == language.lang_name:
            # Optionally: return 204 No Content or a custom message
            return Response(status_code=204)

        language_to_update.lang_name = language.lang_name

        session.commit()
        session.refresh(language_to_update)

        username = get_username_from_token(authorization)
        if username: 

            if language.lang_name:
                note = f"Language '{original_name}' updated to '{language_to_update.lang_name}'"
            else:
                note = f"Language with ID {lang_id} updated to '{language_to_update.lang_name}'"
            log_activity(
                username=username,
                entity_type="Language",
                entity_id=lang_id,
                operation="update",
                note=note
            )

        return Language(
            lang_id=language_to_update.lang_id,
            lang_name=language_to_update.lang_name
        )
    finally:
        session.close()


@language_router.delete("/delete/{lang_id}",response_model=LanguageDelete, summary="Delete a language by ID")
async def delete_language(
        lang_id: int, 
        db: DB = Depends(_get_db),
        authorization: Optional[str] = Header(None)
    ):
    session = db.Session()
    try:
        language_to_delete = session.query(Languages).filter(Languages.lang_id == lang_id).first()
        if language_to_delete is None:
            raise HTTPException(status_code=404, detail="Language not found")
        session.delete(language_to_delete)
        session.commit()

        username = get_username_from_token(authorization)

        if username:
            if language_to_delete.lang_name:
                note = f"Language '{language_to_delete.lang_name}' deleted"
            else:
                note = f"Language with ID {lang_id} deleted"

            log_activity(
                username=username,
                entity_type="Language",
                entity_id=lang_id,
                operation="delete",
                note=f"Language '{language_to_delete.lang_name}' deleted"
            )

        return LanguageDelete(
            lang_id=lang_id
        )

    finally:
        session.close()