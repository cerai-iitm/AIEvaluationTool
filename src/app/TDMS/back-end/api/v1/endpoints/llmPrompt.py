from fastapi import APIRouter, HTTPException, Depends, Header
from schemas import LlmPromptIds, LlmPrompts, LlmPromptCreate, LlmPromptUpdate, LlmPromptDelete
from sqlalchemy.orm import joinedload

from database.fastapi_deps import _get_db
from models import user as user_model
from utils.activity_logger import log_activity
from jose import jwt, JWTError
from config.settings import settings
from typing import Optional
import hashlib

import os
import sys

# Ensure the project 'src' directory is on sys.path so we can import lib.orm and lib.orm.tables modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__),"../../../../../")))

from lib.orm.DB import DB
from lib.orm.tables import Languages, LLMJudgePrompts


llmPrompt_router = APIRouter(prefix="/api/llmPrompts")

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


@llmPrompt_router.get("", response_model=list[LlmPromptIds])
async def list_llmPrompt(db: DB = Depends(_get_db)):
    session = db.Session()
    try:
        llmPrompts = session.query(LLMJudgePrompts).all()
        return [
            LlmPromptIds(
                llmPromptId=llmPrompt.prompt_id,
                prompt=llmPrompt.prompt,
            )
            for llmPrompt in llmPrompts
        ]
    finally:
        session.close()


@llmPrompt_router.get("/all", response_model=list[LlmPrompts])
async def get_llmPrompts(db: DB = Depends(_get_db)):
    session = db.Session()
    try:
        llmPrompts = session.query(LLMJudgePrompts).options(
            joinedload(LLMJudgePrompts.lang)
        ).all()
        return [
            LlmPrompts(
                llmPromptId=llmPrompt.prompt_id,
                prompt=llmPrompt.prompt,
                language=getattr(llmPrompt.lang, "lang_name", None) if llmPrompt.lang else None,
            )
            for llmPrompt in llmPrompts
        ]
    finally:
        session.close()


@llmPrompt_router.get("/{llmPrompt_id}", response_model=LlmPrompts)
async def get_llmPrompt(llmPrompt_id: int, db: DB = Depends(_get_db)):
    session = db.Session()
    try:
        llmPrompt = session.query(LLMJudgePrompts).filter(LLMJudgePrompts.prompt_id == llmPrompt_id).first()
        if not llmPrompt:
            raise HTTPException(status_code=404, detail="LLM Prompt not found")
        return LlmPrompts(
            llmPromptId=llmPrompt.prompt_id,
            prompt=getattr(llmPrompt, "prompt", None),
            language=getattr(llmPrompt.lang, "lang_name", None) if llmPrompt.lang else None,
        )
    finally:
        session.close()


@llmPrompt_router.put("/update/{llmPrompt_id}", response_model=LlmPromptUpdate, summary="Update an LLM prompt by ID")
async def update_llmPrompt(
    llmPrompt_id: int,
    llmPrompt_update: LlmPromptUpdate,
    db: DB = Depends(_get_db),
    authorization: Optional[str] = Header(None)
):
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header missing")

    session = db.Session()
    try:
        llmPrompt = session.query(LLMJudgePrompts).filter(LLMJudgePrompts.prompt_id == llmPrompt_id).first()
        if not llmPrompt:
            raise HTTPException(status_code=404, detail="LLM Prompt not found")

        previous_prompt = llmPrompt.prompt
        previous_language = getattr(llmPrompt.lang, "lang_name", None)

        if llmPrompt_update.prompt is not None:
            llmPrompt.prompt = llmPrompt_update.prompt
        if llmPrompt_update.language is not None:
            language = session.query(Languages).filter(Languages.lang_name == llmPrompt_update.language).first()
            if not language:
                raise HTTPException(status_code=404, detail="Language not found")
            llmPrompt.lang = language

        # Update hash_value if prompt changed
        if llmPrompt_update.prompt is not None:
            hash_input = llmPrompt.prompt or ""
            llmPrompt.hash_value = hashlib.sha256(hash_input.encode("utf-8")).hexdigest()

        session.commit()
        session.refresh(llmPrompt)

        username = get_username_from_token(authorization)
        if not username:
            raise HTTPException(status_code=401, detail="Unauthorized")

        changes = []
        if llmPrompt.prompt != previous_prompt:
            changes.append("prompt updated")
        
        current_language = getattr(llmPrompt.lang, "lang_name", None)
        if current_language != previous_language:
            changes.append("language updated")

        note = f"LLM Prompt {llmPrompt_id} updated"
        if changes:
            note += f": {', '.join(changes)}"
        else:
            note += " (no changes detected)"

        log_activity(
            username=username,
            entity_type="LLM Prompt",
            entity_id=llmPrompt_id,
            operation="update",
            note=note
        )

        return LlmPromptUpdate(
            llmPromptId=llmPrompt.prompt_id,
            prompt=llmPrompt.prompt,
            language=getattr(llmPrompt.lang, "lang_name", None) if llmPrompt.lang else None,
        )
    except HTTPException:
        session.rollback()
        raise
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        session.close()


@llmPrompt_router.post("/create", response_model=LlmPrompts, summary="Create a new LLM prompt")
async def create_llmPrompt(
    llmPrompt_create: LlmPromptCreate,
    db: DB = Depends(_get_db),
    authorization: Optional[str] = Header(None)
):
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header missing")

    session = db.Session()
    try:
        language = session.query(Languages).filter(Languages.lang_name == llmPrompt_create.language).first()
        if not language:
            raise HTTPException(status_code=404, detail="Language not found")

        hash_input = llmPrompt_create.prompt or ""
        hash_value = hashlib.sha256(hash_input.encode("utf-8")).hexdigest()

        existing_ids = [row[0] for row in session.query(LLMJudgePrompts.prompt_id).order_by(LLMJudgePrompts.prompt_id).all()]
        next_id = 1
        for id in existing_ids:
            if id != next_id:
                break
            next_id += 1

        llmPrompt = LLMJudgePrompts(
            prompt_id=next_id,
            prompt=llmPrompt_create.prompt,
            lang=language,
            hash_value=hash_value
        )
        session.add(llmPrompt)
        session.commit()
        session.refresh(llmPrompt)

        username = get_username_from_token(authorization)
        if not username:
            raise HTTPException(status_code=401, detail="Unauthorized")

        note = f"LLM Prompt {llmPrompt.prompt_id} created"
        log_activity(
            username=username,
            entity_type="LLM Prompt",
            entity_id=llmPrompt.prompt_id,
            operation="create",
            note=note
        )

        return LlmPrompts(
            llmPromptId=llmPrompt.prompt_id,
            prompt=llmPrompt.prompt,
            language=llmPrompt.lang.lang_name if llmPrompt.lang else None,
        )
    except HTTPException:
        session.rollback()
        raise
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        session.close()


@llmPrompt_router.delete("/delete/{llmPrompt_id}", response_model=LlmPromptDelete, summary="Delete an LLM prompt by ID")
async def delete_llmPrompt(
    llmPrompt_id: int,
    db: DB = Depends(_get_db),
    authorization: Optional[str] = Header(None)
):
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header missing")

    session = db.Session()
    try:
        llmPrompt = session.query(LLMJudgePrompts).filter(LLMJudgePrompts.prompt_id == llmPrompt_id).first()
        if not llmPrompt:
            raise HTTPException(status_code=404, detail="LLM Prompt not found")

        session.delete(llmPrompt)
        session.commit()

        username = get_username_from_token(authorization)
        if not username:
            raise HTTPException(status_code=401, detail="Unauthorized")

        note = f"LLM Prompt {llmPrompt.prompt_id} deleted"
        log_activity(
            username=username,
            entity_type="LLM Prompt",
            entity_id=llmPrompt.prompt_id,
            operation="delete",
            note=note
        )

        return LlmPromptDelete(
            llmPromptId=llmPrompt_id,
            message="LLM Prompt deleted successfully"
        )
    except HTTPException:
        session.rollback()
        raise
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        session.close()
