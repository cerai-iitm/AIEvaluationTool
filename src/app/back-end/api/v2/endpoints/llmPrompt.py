from typing import List, Optional

from config.settings import settings
from database.fastapi_deps import _get_db
from fastapi import APIRouter, Depends, Header, HTTPException, status
from jose import JWTError, jwt
from schemas.llmPrompt import (
    LlmPromptCreateV2,
    LlmPromptDetailResponse,
    LlmPromptListResponse,
    LlmPromptUpdateV2,
    LlmPromptBase,
)
from sqlalchemy.exc import IntegrityError
from utils.activity_logger import log_activity

from lib.orm.DB import DB
from lib.orm.tables import LLMJudgePrompts

llm_prompt_router = APIRouter(prefix="/api/v2/llm-prompts")


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


@llm_prompt_router.get(
    "",
    response_model=List[LlmPromptListResponse],
    summary="List all LLM prompts (v2)",
)
def list_llm_prompts(db: DB = Depends(_get_db)):
    llmjudgeprompt = db.llmjudgeprompts
    return [
        LlmPromptListResponse(
            llmPromptId=llm.prompt_id,
            prompt=llm.prompt,
            language=db.get_language_name(llm.lang_id)
        )
        for llm in llmjudgeprompt
    ]



# @llm_prompt_router.get(
#     "",
#     response_model=List[LlmPromptListResponse],
#     summary="List all LLM prompts (v2)",
# )
# def list_llm_prompts(db: DB = Depends(_get_db)):
#    return db.list_llm_prompts_with_metadata() or []


@llm_prompt_router.get(
    "/{llm_prompt_id}", 
    response_model=LlmPromptDetailResponse,
    summary="Get an LLM prompt by ID (v2)",
)
def get_llm_prompt(llm_prompt_id: int, db: DB = Depends(_get_db)):
    llm_prompt = db.get_llm_prompt_by_id(llm_prompt_id)
    if llm_prompt is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"LLM prompt with ID {llm_prompt_id} not found",
        )
    # Assuming language name can be fetched via relation or method, else None
    #language_name = getattr(llm_prompt.language, "lang_name", None) if hasattr(llm_prompt, "language") else None

    language_name = db.get_language_name(llm_prompt.lang_id)

    return LlmPromptDetailResponse(
        llmPromptId=llm_prompt.prompt_id,
        prompt=llm_prompt.prompt,
        language=language_name,
    )

# @llm_prompt_router.get(
#     "/{llm_prompt_id}",
#     response_model=LlmPromptDetailResponse,
#     summary="Get an LLM prompt by ID (v2)",
# )
# def get_llm_prompt(llm_prompt_id: int, db: DB = Depends(_get_db)):
#     llm_prompt = db.get_llm_prompt_with_metadata(llm_prompt_id)
#     if llm_prompt is None:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND, detail="LLM prompt not found"
#         )
#     return llm_prompt


@llm_prompt_router.post(
    "/create",
    response_model=LlmPromptDetailResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new LLM prompt (v2)",
)
def create_llm_prompt(
    llmPrompt: LlmPromptBase,
    db: DB = Depends(_get_db),
    authorization: Optional[str] = Header(None),
):
    try:
        with db.Session() as session:
            existing_ids = [row[0] for row in session.query(LLMJudgePrompts.prompt_id).order_by(LLMJudgePrompts.prompt_id).all()]
            next_id = 1
            for id in existing_ids:
                if id != next_id:
                    break
                next_id += 1

        lang_id = db.add_or_get_language_id(llmPrompt.language)

        llm_prompt_obj = db._DB__add_or_get_llm_judge_prompt_custom_id(llmPrompt.prompt, next_id, lang_id)
        if llm_prompt_obj is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="An LLM prompt with the same content already exists.",
            )
        
        username = _get_username_from_token(authorization)
        if username:
            log_activity(
                username=username,
                entity_type="LLM Prompt",
                entity_id=llm_prompt_obj.prompt_id,
                operation="create",
                note=f"Created LLM prompt with ID {llm_prompt_obj.prompt_id}",
            )

        return LlmPromptDetailResponse(
            llmPromptId=llm_prompt_obj.prompt_id,
            prompt=llm_prompt_obj.prompt,
            language=llmPrompt.language,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))



# @llm_prompt_router.post(
#     "/create",
#     response_model=LlmPromptDetailResponse,
#     status_code=status.HTTP_201_CREATED,
#     summary="Create a new LLM prompt (v2)",
# )
# def create_llm_prompt(
#     payload: LlmPromptCreateV2,
#     db: DB = Depends(_get_db),
#     authorization: Optional[str] = Header(None),
# ):
#     try:
#         llm_prompt_id = db.create_llm_prompt_v2(payload.model_dump())
#     except IntegrityError:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail="An LLM prompt with the same content already exists.",
#         )
#     except ValueError as e:
#         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

#     created = db.get_llm_prompt_with_metadata(llm_prompt_id)
#     if created is None:
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail="LLM prompt created but could not be loaded.",
#         )

#     username = _get_username_from_token(authorization)
#     if username:
#         log_activity(
#             username=username,
#             entity_type="LLM Prompt",
#             entity_id=str(created["llmPromptId"]),
#             operation="create",
#             note=f"LLM Prompt '{created['llmPromptId']}' created (v2)",
#         )

#     return created


@llm_prompt_router.put(
    "/update/{llm_prompt_id}",
    response_model=LlmPromptDetailResponse,
    summary="Update an LLM prompt (v2)",
)
def update_llm_prompt_v2(
    llm_prompt_id: int,
    payload: LlmPromptUpdateV2,
    db: DB = Depends(_get_db),
    authorization: Optional[str] = Header(None),
):
    update_data = payload.model_dump(exclude_unset=True)
    if not update_data:
        existing = db.get_llm_prompt_by_id(llm_prompt_id)
        if existing is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="LLM prompt not found"
            )

        #existing_prompt = 
        
        language_name = db.get_language_name(existing.lang_id)
        if payload.prompt is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Prompt cannot be empty",
            )

        # return LlmPromptDetailResponse(
        #     llmPromptId=existing.prompt_id,
        #     prompt=existing.prompt,
        #     language=language_name,
        # )

    try:
        updated = db.update_llm_prompt_v2(llm_prompt_id, update_data)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        ) from exc

    if updated is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="LLM prompt not found"
        )

    username = _get_username_from_token(authorization)
    if username:
        log_activity(
            username=username,
            entity_type="LLM Prompt",
            entity_id=str(updated.prompt_id),
            operation="update",
            note="LLM prompt updated via v2 endpoint",
        )

    return LlmPromptDetailResponse(
        llmPromptId=updated.prompt_id,
        prompt=updated.prompt,
        language=getattr(updated.lang, "lang_name", None) if updated.lang else None,
    ) 


@llm_prompt_router.delete(
    "/delete/{llm_prompt_id}",
    summary="Delete an LLM prompt (v2)",
)
def delete_llm_prompt(
    llm_prompt_id: int,
    db: DB = Depends(_get_db),
    authorization: Optional[str] = Header(None),
):
    existing = db.get_llm_prompt_by_id(llm_prompt_id)
    if existing is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="LLM prompt not found"
        )

    if not db.delete_llm_prompt_record(llm_prompt_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="LLM prompt not found"
        )

    username = _get_username_from_token(authorization)
    if username:
        log_activity(
            username=username,
            entity_type="LLM Prompt",
            entity_id=str(existing.prompt_id),
            operation="delete",
            note=f"LLM Prompt '{existing.prompt_id}' deleted (v2)",
        )

    return {"message": "LLM prompt deleted successfully"}
