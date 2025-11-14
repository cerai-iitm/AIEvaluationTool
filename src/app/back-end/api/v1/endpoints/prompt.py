from fastapi import APIRouter, HTTPException, Depends, Header
from schemas import PromptIds, Prompts, PromptCreate, PromptUpdate, PromptDelete
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
#sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../database")))

from lib.orm.DB import DB
from lib.orm.tables import Domains, Languages, Prompts as PromptsTable


prompt_router = APIRouter(prefix="/api/prompts")

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


@prompt_router.get("", response_model=list[PromptIds])
async def list_prompts(db: DB = Depends(_get_db)):
    session = db.Session()
    try:
        prompts = session.query(PromptsTable).all()
        return [
            PromptIds(
                prompt_id=getattr(prompt, "prompt_id", None),
                user_prompt=getattr(prompt, "user_prompt", None),
                system_prompt=getattr(prompt, "system_prompt", None),
            )
            for prompt in prompts
        ]
    finally:
        session.close()


@prompt_router.get("/all", response_model=list[Prompts])
async def get_prompts(db: DB = Depends(_get_db)):
    session = db.Session()
    try:
        prompts = session.query(PromptsTable).options(
            joinedload(PromptsTable.lang),
            joinedload(PromptsTable.domain)
        ).all()
        return [
            Prompts(
                prompt_id=prompt.prompt_id,
                user_prompt=prompt.user_prompt,
                system_prompt=prompt.system_prompt,
                language=getattr(prompt.lang, "lang_name", None) if prompt.lang else None,
                domain=getattr(prompt.domain, "domain_name", None) if prompt.domain else None,
            )
            for prompt in prompts
        ]
    finally:
        session.close()

@prompt_router.get("/{prompt_id}", response_model=Prompts)
async def get_prompt(prompt_id: int, db: DB = Depends(_get_db)):
    session = db.Session()
    try:
        prompt = session.query(PromptsTable).filter(PromptsTable.prompt_id == prompt_id).first()
        if not prompt:
            raise HTTPException(status_code=404, detail="Prompt not found")
        return Prompts(
            prompt_id=prompt.prompt_id,
            user_prompt=getattr(prompt, "user_prompt", None),
            system_prompt=getattr(prompt, "system_prompt", None),
            language=getattr(prompt.lang, "lang_name", None) if prompt.lang else None,
            domain=getattr(prompt.domain, "domain_name", None) if prompt.domain else None
        )
    finally:
        session.close()


@prompt_router.put("/update/{prompt_id}", response_model=PromptUpdate, summary="Update a prompt by ID")
async def update_prompt(
    prompt_id: int,
    prompt_update: PromptUpdate,
    db: DB = Depends(_get_db),
    authorization: Optional[str] = Header(None)
):
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header missing")

    session = db.Session()
    try:
        prompt = session.query(PromptsTable).filter(PromptsTable.prompt_id == prompt_id).first()
        if not prompt:
            raise HTTPException(status_code=404, detail="Prompt not found")

        previous_user_prompt = prompt.user_prompt
        previous_system_prompt = prompt.system_prompt
        previous_language = getattr(prompt.lang, "lang_name", None)
        previous_domain = getattr(prompt.domain, "domain_name", None)

        if prompt_update.user_prompt is not None:
            prompt.user_prompt = prompt_update.user_prompt
        if prompt_update.system_prompt is not None:
            prompt.system_prompt = prompt_update.system_prompt
        if prompt_update.language is not None:
            language = session.query(Languages).filter(Languages.lang_name == prompt_update.language).first()
            if not language:
                raise HTTPException(status_code=404, detail="Language not found")
            prompt.lang = language
        if prompt_update.domain is not None:
            domain = session.query(Domains).filter(Domains.domain_name == prompt_update.domain).first()
            if not domain:
                raise HTTPException(status_code=404, detail="Domain not found")
            prompt.domain = domain

        session.commit()
        session.refresh(prompt)

        username = get_username_from_token(authorization)
        if not username:
            raise HTTPException(status_code=401, detail="Unauthorized")

        changes = []
        if prompt.user_prompt != previous_user_prompt:
            changes.append("user prompt updated")
        if prompt.system_prompt != previous_system_prompt:
            changes.append("system prompt updated")

        current_language = getattr(prompt.lang, "lang_name", None)
        if current_language != previous_language:
            changes.append("language updated")

        current_domain = getattr(prompt.domain, "domain_name", None)
        if current_domain != previous_domain:
            changes.append("domain updated")

        note = f"Prompt {prompt_id} updated"
        if changes:
            note += f": {', '.join(changes)}"
        else:
            note += " (no changes detected)"

        log_activity(
            username=username,
            entity_type="Prompt",
            entity_id=prompt_id,
            operation="update",
            note=note
        )

        return PromptUpdate(
            prompt_id=prompt.prompt_id,
            user_prompt=prompt.user_prompt,
            system_prompt=prompt.system_prompt,
            language=getattr(prompt.lang, "lang_name", None) if prompt.lang else None,
            domain=getattr(prompt.domain, "domain_name", None) if prompt.domain else None,
        )
    except HTTPException:
        session.rollback()
        raise
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        session.close()


@prompt_router.post("/create", response_model=Prompts, summary="Create a new prompt")
async def create_prompt(
    prompt_create: PromptCreate,
    db: DB = Depends(_get_db),
    authorization: Optional[str] = Header(None)
):
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header missing")

    session = db.Session()
    try:
        language = session.query(Languages).filter(Languages.lang_name == prompt_create.language).first()
        if not language:
            raise HTTPException(status_code=404, detail="Language not found")

        domain = session.query(Domains).filter(Domains.domain_name == prompt_create.domain).first()
        if not domain:
            raise HTTPException(status_code=404, detail="Domain not found")

        hash_input = "|".join(
            [
                prompt_create.user_prompt or "",
                prompt_create.system_prompt or "",

            ]
        )
        hash_value = hashlib.sha256(hash_input.encode("utf-8")).hexdigest()

        existing_ids = [row[0] for row in session.query(PromptsTable.prompt_id).order_by(PromptsTable.prompt_id).all()]
        next_id = 1
        for id in existing_ids:
            if id != next_id:
                break
            next_id += 1

        prompt = PromptsTable(
            prompt_id=next_id,
            user_prompt=prompt_create.user_prompt,
            system_prompt=prompt_create.system_prompt,
            lang=language,
            domain=domain,
            hash_value=hash_value
        )
        session.add(prompt)
        session.commit()
        session.refresh(prompt)

        username = get_username_from_token(authorization)
        if not username:
            raise HTTPException(status_code=401, detail="Unauthorized")

        note = f"Prompt {prompt.prompt_id} created"
        log_activity(
            username=username,
            entity_type="Prompt",
            entity_id=prompt.prompt_id,
            operation="create",
            note=note
        )

        return Prompts(
            prompt_id=prompt.prompt_id,
            user_prompt=prompt.user_prompt,
            system_prompt=prompt.system_prompt,
            language=prompt.lang.lang_name if prompt.lang else None,
            domain=prompt.domain.domain_name if prompt.domain else None
        )
    except HTTPException:
        session.rollback()
        raise
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        session.close() 


@prompt_router.delete("/delete/{prompt_id}", response_model=PromptDelete, summary="Delete a prompt by ID")
async def delete_prompt(
    prompt_id: int,
    db: DB = Depends(_get_db),
    authorization: Optional[str] = Header(None)
):
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header missing")

    session = db.Session()
    try:
        prompt = session.query(PromptsTable).filter(PromptsTable.prompt_id == prompt_id).first()
        if not prompt:
            raise HTTPException(status_code=404, detail="Prompt not found")

        session.delete(prompt)
        session.commit()

        username = get_username_from_token(authorization)
        if not username:
            raise HTTPException(status_code=401, detail="Unauthorized")

        note = f"Prompt {prompt.prompt_id} deleted"
        log_activity(
            username=username,
            entity_type="Prompt",
            entity_id=prompt.prompt_id,
            operation="delete",
            note=note
        )

        return PromptDelete(
            prompt_id=prompt_id,
            message="Prompt deleted successfully"
        )
    except HTTPException:
        session.rollback()
        raise
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        session.close()