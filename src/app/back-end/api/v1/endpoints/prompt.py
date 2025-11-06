from fastapi import APIRouter, HTTPException, Depends
from schemas import PromptIds
from sqlalchemy.orm import joinedload

import os
import sys

# Ensure the project 'src' directory is on sys.path so we can import lib.orm and lib.orm.tables modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__),"../../../../../")))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../database")))

from lib.orm.DB import DB
from lib.orm.tables import Prompts
from database.fastapi_deps import get_db

prompt_router = APIRouter(prefix="/api/prompts")



@prompt_router.get("", response_model=list[PromptIds])
async def list_prompts(db: DB = Depends(get_db)):
    session = db.Session()
    try:
        prompts = session.query(Prompts).all()
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
