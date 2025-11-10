from fastapi import APIRouter, HTTPException, Depends
from schemas import PromptIds, Prompts
from sqlalchemy.orm import joinedload

import os
import sys

# Ensure the project 'src' directory is on sys.path so we can import lib.orm and lib.orm.tables modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__),"../../../../../")))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../database")))

from lib.orm.DB import DB
from lib.orm.tables import Prompts as PromptsTable
from database.fastapi_deps import _get_db

prompt_router = APIRouter(prefix="/api/prompts")



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
