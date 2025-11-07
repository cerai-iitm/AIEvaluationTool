from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
from schemas import LlmPromptIds
import os
import sys

# Ensure the project 'src' directory is on sys.path so we can import lib.orm
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../../")))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../database")))

from lib.orm.DB import DB
from lib.orm.tables import LLMJudgePrompts
from database.fastapi_deps import _get_db

llmPrompt_router = APIRouter(prefix="/api/llmPrompt")

@llmPrompt_router.get("", response_model=list[LlmPromptIds])
async def get_llmPrompt(db: DB = Depends(_get_db)):
    session = db.Session()
    try:
        llmPrompts = session.query(LLMJudgePrompts).all()
        return [
            LlmPromptIds(
                prompt_id=getattr(llmPrompt, "prompt_id", None),
                prompt=getattr(llmPrompt, "prompt", None),
            )
            for llmPrompt in llmPrompts
        ]
    finally:
        session.close()