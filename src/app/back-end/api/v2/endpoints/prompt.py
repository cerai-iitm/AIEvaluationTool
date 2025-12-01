from typing import List, Optional

from config.settings import settings
from database.fastapi_deps import _get_db
from fastapi import APIRouter, Depends, Header, HTTPException, status
from jose import JWTError, jwt
from schemas.prompt import (
    PromptCreateV2,
    PromptDetailResponse,
    PromptListResponse,
    PromptUpdateV2,
)
from sqlalchemy.exc import IntegrityError
from utils.activity_logger import log_activity

from lib.orm.DB import DB
from lib.orm.tables import Prompts as PromptsTable

prompt_router = APIRouter(prefix="/api/v2/prompts")


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
        prompt = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )
        return prompt.get("user_name")
    except JWTError:
        return None


@prompt_router.get(
    "",
    response_model=List[PromptDetailResponse],
    summary="List all prompts (v2)",
)
def list_prompts(db: DB = Depends(_get_db)):
    prompts = db.prompts
    if prompts is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Prompts not found"
        )
    return [
        PromptDetailResponse(
            prompt_id=prompt.prompt_id,
            user_prompt=prompt.user_prompt,
            system_prompt=prompt.system_prompt,
            language = prompt.lang.lang_name if prompt.lang else None,
            domain = prompt.domain.domain_name if prompt.domain else None
        )
        for prompt in prompts
    ]


# @prompt_router.get(
#     "",
#     response_model=List[PromptListResponse],
#     summary="List all prompts (v2)",
# )
# def list_prompts(db: DB = Depends(_get_db)):
#     return db.list_prompts_with_metadata() or []


@prompt_router.get(
    "/{prompt_id:int}",
    response_model=PromptDetailResponse,
    summary="Get a prompt by ID (v2)",
)
def get_prompt(prompt_id: int, db: DB = Depends(_get_db)):
    prompt = db.get_prompt(prompt_id)
    if prompt is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Prompt not found"
        )

    language = db.get_language_name(prompt.lang_id)

    if language is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Language not found"
        )

    domain = db.get_domain_name(prompt.domain_id)

    if domain is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Domain not found"
        )

    return PromptDetailResponse(
        prompt_id = prompt.prompt_id,
        user_prompt = prompt.user_prompt,
        system_prompt = prompt.system_prompt,
        language = language,
        domain = domain
    )


# @prompt_router.get(
#     "/{prompt_id}",
#     response_model=PromptDetailResponse,
#     summary="Get a prompt by ID (v2)",
# )
# def get_prompt(prompt_id: int, db: DB = Depends(_get_db)):
#     prompt = db.get_prompt_with_metadata(prompt_id)
#     if prompt is None:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND, detail="Prompt not found"
#         )
#     return prompt


@prompt_router.post(
    "/create",
    response_model=PromptDetailResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new prompt (v2)",
)
def create_prompt(
    prompt: PromptCreateV2,
    db: DB = Depends(_get_db),
    authorization: Optional[str] = Header(None),
):
    #try:
    with db.Session() as session:
        try:
            existing_ids = [row[0] for row in session.query(PromptsTable.prompt_id).order_by(PromptsTable.prompt_id).all()]
            next_id = 1
            for id in existing_ids:
                if id != next_id:
                    break
                next_id += 1

            lang_id = db.add_or_get_language_id(prompt.language)
            domain_id = db.add_or_get_domain_id(prompt.domain)   

            # Import and create Prompt data class instance
            from lib.data.prompt import Prompt as PromptData
            prompt_data = PromptData(
                user_prompt=prompt.user_prompt,
                system_prompt=prompt.system_prompt
            )

            prompt_obj = db._DB__add_or_get_prompt_custom_Id(prompt_data, next_id, domain_id, lang_id)         
            if prompt_obj is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="A prompt with the same content already exists.",
                )
            username = _get_username_from_token(authorization)
            if username:
                log_activity(
                    username=username,
                    entity_type="prompt",
                    entity_id = prompt_obj.prompt_id,
                    operation="create",
                    note=f"Created prompt with ID {prompt_obj.prompt_id}",
                )
            
            return PromptDetailResponse(
                prompt_id = prompt_obj.prompt_id,
                user_prompt = prompt_obj.user_prompt,
                system_prompt = prompt_obj.system_prompt,
                language = prompt.language,
                domain = prompt.domain
            )

        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))



# @prompt_router.post(
#     "/create",
#     response_model=PromptDetailResponse,
#     status_code=status.HTTP_201_CREATED,
#     summary="Create a new prompt (v2)",
# )
# def create_prompt(
#     prompt: PromptCreateV2,
#     db: DB = Depends(_get_db),
#     authorization: Optional[str] = Header(None),
# ):
#     try:
#         prompt_id = db.create_prompt_v2(prompt.model_dump())
#     except IntegrityError:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail="A prompt with the same content already exists.",
#         )
#     except ValueError as e:
#         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

#     created = db.get_prompt_with_metadata(prompt_id)
#     if created is None:
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail="Prompt created but could not be loaded.",
#         )

#     username = _get_username_from_token(authorization)
#     if username:
#         log_activity(
#             username=username,
#             entity_type="Prompt",
#             entity_id=str(created["prompt_id"]),
#             operation="create",
#             note=f"Prompt '{created['prompt_id']}' created (v2)",
#         )

#     return created


@prompt_router.put(
    "/update/{prompt_id:int}",
    response_model=PromptDetailResponse,
    summary="Update a prompt (v2)",
)
def update_prompt_v2(
    prompt_id: int,
    payload: PromptUpdateV2,
    db: DB = Depends(_get_db),
    authorization: Optional[str] = Header(None),
):
    update_data = payload.model_dump(exclude_unset=True)
    if not update_data:
        existing = db.get_prompt(prompt_id)
        if existing is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Prompt not found"
            )
        language_name = db.get_language_name(existing.lang_id)
        domain_name = db.get_domain_name(existing.domain_id)
        return PromptDetailResponse(
            prompt_id=existing.prompt_id,
            user_prompt=existing.user_prompt,
            system_prompt=existing.system_prompt,
            language=language_name,
            domain=domain_name,
        )

    try:
        updated = db.update_prompt_v2(prompt_id, update_data)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        ) from exc

    if updated is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Prompt not found"
        )

    username = _get_username_from_token(authorization)
    if username:
        changes = []
        if "prompt" in update_data or "user_prompt" in update_data or "system_prompt" in update_data:
            changes.append("prompt updated")
        if "language" in update_data:
            changes.append("language updated")
        if "domain" in update_data:
            changes.append("domain updated")

        note = f"Prompt {prompt_id} updated"
        if changes:
            note += f": {', '.join(changes)}"
        else:
            note += " (no changes detected)"
        log_activity(
            username=username,
            entity_type="Prompt",
            entity_id=str(updated.prompt_id),
            operation="update",
            note=note,
        ) 

    return PromptDetailResponse(
        prompt_id=updated.prompt_id,
        user_prompt=updated.user_prompt,
        system_prompt=updated.system_prompt,
        language=getattr(updated.lang, "lang_name", None) if updated.lang else None,
        domain=getattr(updated.domain, "domain_name", None) if updated.domain else None,
    )


@prompt_router.delete(
    "/delete/{prompt_id}",
    summary="Delete a prompt (v2)",
)
def delete_prompt(
    prompt_id: int,
    db: DB = Depends(_get_db),
    authorization: Optional[str] = Header(None),
):
    existing = db.get_prompt(prompt_id)
    if existing is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Prompt not found"
        )

    if not db.delete_prompt_record(prompt_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Prompt not found"
        )

    username = _get_username_from_token(authorization)
    if username:
        log_activity(
            username=username,
            entity_type="Prompt",
            entity_id=str(existing.prompt_id),
            operation="delete",
            note=f"Prompt '{existing.prompt_id}' deleted",
        )

    return {"message": "Prompt deleted successfully"} 
