from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import joinedload
from schemas import LlmPromptIds, LlmPrompts
import os
import sys

# Ensure the project 'src' directory is on sys.path so we can import lib.orm
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../../")))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../database")))

from lib.orm.DB import DB
from lib.orm.tables import LLMJudgePrompts
from database.fastapi_deps import _get_db

llmPrompt_router = APIRouter(prefix="/api/llmPrompts")

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