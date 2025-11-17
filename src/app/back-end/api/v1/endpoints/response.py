from fastapi import APIRouter, HTTPException, Depends, Header
from fastapi.responses import JSONResponse
from schemas import Response, ResponseIds, Responses, ResponseUpdate, ResponseCreate
from enum import Enum
from typing import Optional
import os
import sys
from sqlalchemy.orm import joinedload
import hashlib
from jose import jwt, JWTError
from config.settings import settings
from utils.activity_logger import log_activity

# Ensure the project 'src' directory is on sys.path so we can import lib.orm
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../../")))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../database")))

from lib.orm.DB import DB
from lib.orm.tables import Prompts, TestCases, Languages, Responses as ResponsesTable
from database.fastapi_deps import _get_db

response_router = APIRouter(prefix="/api/responses")

def get_username_from_token(authorization: Optional[str] = None) -> Optional[str]:
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


# Define the response types as an Enum for easy reference
class ResponseTypeEnum(str, Enum):
    GT = 'GT'
    GTDesc = 'GTDesc'
    NA = 'NA'

@response_router.get("/response/types", response_model=list[ResponseTypeEnum], summary="Get all response types")
def get_response_types(db: DB = Depends(_get_db)):
    return list(ResponseTypeEnum)


@response_router.get("/", response_model=list[ResponseIds], summary="Get all response IDs")
async def list_responses(db: DB = Depends(_get_db)):
    session = db.Session()
    try:
        responses = session.query(ResponsesTable).all()
        return [
            ResponseIds(
                response_id=getattr(r, "response_id", None),
                response_text=getattr(r, "response_text", None),
            )
            for r in responses
        ]
    finally:
        session.close()


@response_router.get("/all", response_model=list[Responses], summary="Get all responses with full details")
async def get_responses(db: DB = Depends(_get_db)):
    session = db.Session()
    try:
        responses = session.query(ResponsesTable).options(
            joinedload(ResponsesTable.prompt),
            joinedload(ResponsesTable.lang)
        ).all()
        return [
            Responses(
                response_id=r.response_id,
                response_text=r.response_text,
                response_type=r.response_type,
                user_prompt=getattr(r.prompt, "user_prompt", None) if r.prompt else None,
                system_prompt=getattr(r.prompt, "system_prompt", None) if r.prompt else None,
                lang_name=getattr(r.lang, "lang_name", None) if r.lang else None,
            )
            for r in responses
        ]
    finally:
        session.close()


@response_router.get("/{response_id}", response_model=Responses, summary="Get a response by ID")
async def get_response(response_id: int, db: DB = Depends(_get_db)):
    session = db.Session()
    try:
        response = session.query(ResponsesTable).options(
            joinedload(ResponsesTable.prompt),
            joinedload(ResponsesTable.lang)
        ).filter(ResponsesTable.response_id == response_id).first()
        
        if response is None:
            raise HTTPException(status_code=404, detail="Response not found")
        
        return Responses(
            response_id=response.response_id,
            response_text=response.response_text,
            response_type=response.response_type,
            user_prompt=getattr(response.prompt, "user_prompt", None) if response.prompt else None,
            system_prompt=getattr(response.prompt, "system_prompt", None) if response.prompt else None,
            lang_name=getattr(response.lang, "lang_name", None) if response.lang else None
        )
    finally:
        session.close()


@response_router.put("/update/{response_id}", response_model=Responses, summary="Update a response by ID")
async def update_response(
    response_id: int, 
    response_update: ResponseUpdate, 
    db: DB = Depends(_get_db),
    authorization: Optional[str] = Header(None)
):
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header missing")

    session = db.Session()
    try:
        response = session.query(ResponsesTable).options(
            joinedload(ResponsesTable.prompt),
            joinedload(ResponsesTable.lang)
        ).filter(ResponsesTable.response_id == response_id).first()
        
        if response is None:
            raise HTTPException(status_code=404, detail="Response not found")

        original_text = response.response_text
        changes = []

        # Update response text if provided
        if response_update.response_text is not None and response_update.response_text.strip():
            if response.response_text != response_update.response_text:
                # Compute hash for response
                response_str = f"Response Text: '{response_update.response_text}'\tResponse Type: '{response.response_type}'"
                hashing = hashlib.sha1()
                hashing.update(response_str.encode('utf-8'))
                new_hash = hashing.hexdigest()

                # Check if a response with this hash already exists (excluding current response)
                existing_response = session.query(ResponsesTable).filter(
                    ResponsesTable.hash_value == new_hash,
                    ResponsesTable.response_id != response_id
                ).first()

                if existing_response:
                    raise HTTPException(
                        status_code=400, 
                        detail="A response with this text already exists"
                    )
                
                response.response_text = response_update.response_text
                response.hash_value = new_hash
                changes.append("text updated")

        # Update response type if provided
        if response_update.response_type is not None:
            if response.response_type != response_update.response_type:
                response.response_type = response_update.response_type
                # Recompute hash with new response type
                response_str = f"Response Text: '{response.response_text}'\tResponse Type: '{response.response_type}'"
                hashing = hashlib.sha1()
                hashing.update(response_str.encode('utf-8'))
                response.hash_value = hashing.hexdigest()
                changes.append("type updated")

        # Update language if provided
        if response_update.lang_name is not None:
            lang = session.query(Languages).filter(Languages.lang_name == response_update.lang_name).first()
            if lang is None:
                raise HTTPException(status_code=404, detail=f"Language '{response_update.lang_name}' not found")
            if response.lang_id != lang.lang_id:
                response.lang_id = lang.lang_id
                changes.append("language updated")

        # Update prompt fields if provided
        if response_update.user_prompt is not None or response_update.system_prompt is not None:
            user_prompt_changed = response_update.user_prompt is not None and (
                not response.prompt or response_update.user_prompt != response.prompt.user_prompt
            )
            system_prompt_changed = response_update.system_prompt is not None and (
                not response.prompt or response_update.system_prompt != (response.prompt.system_prompt or "")
            )
            
            if user_prompt_changed or system_prompt_changed:
                new_user_prompt = response_update.user_prompt if response_update.user_prompt is not None else (
                    response.prompt.user_prompt if response.prompt else ""
                )
                new_system_prompt = response_update.system_prompt if response_update.system_prompt is not None else (
                    response.prompt.system_prompt if response.prompt else ""
                )

                # Compute hash the same way as in Prompt.digest
                system_prompt_value = new_system_prompt.strip() if new_system_prompt else ""
                prompt_str = f"System: '{system_prompt_value}'\tUser: '{new_user_prompt}'"
                hashing = hashlib.sha1()
                hashing.update(prompt_str.encode('utf-8'))
                new_hash = hashing.hexdigest()

                # Check if a prompt with this hash already exists
                existing_prompt = session.query(Prompts).filter(
                    Prompts.hash_value == new_hash
                ).first()

                if existing_prompt:
                    # If a prompt with this hash exists, point response to that prompt
                    response.prompt_id = existing_prompt.prompt_id
                else:
                    # Create or update prompt
                    if response.prompt:
                        # Update existing prompt
                        if user_prompt_changed:
                            response.prompt.user_prompt = new_user_prompt
                        if system_prompt_changed:
                            response.prompt.system_prompt = system_prompt_value if system_prompt_value else None
                        response.prompt.hash_value = new_hash
                    else:
                        # Create new prompt - need lang_id and domain_id
                        default_lang = session.query(Languages).first()
                        if not default_lang:
                            raise HTTPException(
                                status_code=500, 
                                detail="No languages found in database. Please add a language first."
                            )
                        
                        from lib.orm.tables import Domains
                        default_domain = session.query(Domains).first()
                        if not default_domain:
                            raise HTTPException(
                                status_code=500, 
                                detail="No domains found in database. Please add a domain first."
                            )

                        new_prompt = Prompts(
                            user_prompt=new_user_prompt,
                            system_prompt=system_prompt_value if system_prompt_value else None,
                            lang_id=default_lang.lang_id,
                            domain_id=default_domain.domain_id,
                            hash_value=new_hash
                        )
                        session.add(new_prompt)
                        session.flush()
                        response.prompt_id = new_prompt.prompt_id
                
                changes.append("prompt updated")

        session.commit()
        session.refresh(response)

        # Log the activity
        username = get_username_from_token(authorization)
        if username:

            changes = []

            if response_update.response_text is not None and response_update.response_text != original_name:
                changes.append(f"text changed")
            if response_udpate.user_prompt is not None or response_update.system_prompt is not None:
                changes.append("prompt updated")
            if response_update.response_type is not None:
                changes.append("type updated")
            if response_update.lang is not None:
                changes.append("language updated")

            note = f"Response '{response.response_id}' updated"
            if changes:
                note += f": {', '.join(changes)}"
            else:
                note += " (no changes detected)"

            log_activity(
                username=username,
                entity_type="Response",
                entity_id=str(response.response_id),
                operation="update",
                note=note
            )

        # Reload with relationships
        session.refresh(response)
        response = session.query(ResponsesTable).options(
            joinedload(ResponsesTable.prompt),
            joinedload(ResponsesTable.lang)
        ).filter(ResponsesTable.response_id == response_id).first()

        return Responses(
            response_id=response.response_id,
            response_text=response.response_text,
            response_type=response.response_type,
            user_prompt=getattr(response.prompt, "user_prompt", None) if response.prompt else None,
            system_prompt=getattr(response.prompt, "system_prompt", None) if response.prompt else None,
            lang_name=getattr(response.lang, "lang_name", None) if response.lang else None
        )
    except HTTPException:
        session.rollback()
        raise
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Error updating response: {str(e)}")
    finally:
        session.close()


@response_router.post("/create", response_model=Responses, summary="Create a new response")
async def create_response(
    response_create: ResponseCreate, 
    db: DB = Depends(_get_db),
    authorization: Optional[str] = Header(None)
):
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header missing")

    session = db.Session()
    try:
        # Validate response text is not empty
        if not response_create.response_text or not response_create.response_text.strip():
            raise HTTPException(status_code=400, detail="Response text is required")

        # Validate response type
        if response_create.response_type not in ['GT', 'GTDesc', 'NA']:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid response type. Must be one of: GT, GTDesc, NA"
            )

        # Check if response text already exists (optional - you might want to allow duplicates)
        # For now, we'll allow duplicates but check hash uniqueness

        # Find or create Prompt
        system_prompt_value = response_create.system_prompt.strip() if response_create.system_prompt else ""
        system_prompt_db = system_prompt_value if system_prompt_value else None
        
        prompt_str = f"System: '{system_prompt_value}'\tUser: '{response_create.user_prompt}'"
        hashing = hashlib.sha1()
        hashing.update(prompt_str.encode('utf-8'))
        prompt_hash = hashing.hexdigest()

        existing_prompt = session.query(Prompts).filter(
            Prompts.hash_value == prompt_hash
        ).first()

        if existing_prompt:
            prompt_id = existing_prompt.prompt_id
        else:
            # Create new prompt
            default_lang = session.query(Languages).first()
            if not default_lang:
                raise HTTPException(
                    status_code=500, 
                    detail="No languages found in database. Please add a language first."
                )
            
            from lib.orm.tables import Domains
            default_domain = session.query(Domains).first()
            if not default_domain:
                raise HTTPException(
                    status_code=500, 
                    detail="No domains found in database. Please add a domain first."
                )

            new_prompt = Prompts(
                user_prompt=response_create.user_prompt,
                system_prompt=system_prompt_db,
                lang_id=default_lang.lang_id,
                domain_id=default_domain.domain_id,
                hash_value=prompt_hash
            )
            session.add(new_prompt)
            session.flush()
            prompt_id = new_prompt.prompt_id

        # Find language
        lang = session.query(Languages).filter(Languages.lang_name == response_create.lang_name).first()
        if lang is None:
            raise HTTPException(status_code=404, detail=f"Language '{response_create.lang_name}' not found")
        lang_id = lang.lang_id

        # Compute hash for response
        response_str = f"Response Text: '{response_create.response_text}'\tResponse Type: '{response_create.response_type}'"
        hashing = hashlib.sha1()
        hashing.update(response_str.encode('utf-8'))
        response_hash = hashing.hexdigest()

        # Check if response with this hash already exists
        existing_response = session.query(ResponsesTable).filter(
            ResponsesTable.hash_value == response_hash
        ).first()

        if existing_response:
            raise HTTPException(
                status_code=400, 
                detail="A response with this text and type already exists"
            )

        # Create new response
        new_response = ResponsesTable(
            response_text=response_create.response_text,
            response_type=response_create.response_type,
            prompt_id=prompt_id,
            lang_id=lang_id,
            hash_value=response_hash
        )
        session.add(new_response)
        session.commit()
        session.refresh(new_response)

        # Log the activity
        username = get_username_from_token(authorization)
        if username:
            log_activity(
                username=username,
                entity_type="Response",
                entity_id=str(new_response.response_id),
                operation="create",
                note=f"Response '{new_response.response_id}' created"
            )

        # Reload with relationships
        response = session.query(ResponsesTable).options(
            joinedload(ResponsesTable.prompt),
            joinedload(ResponsesTable.lang)
        ).filter(ResponsesTable.response_id == new_response.response_id).first()

        return Responses(
            response_id=response.response_id,
            response_text=response.response_text,
            response_type=response.response_type,
            user_prompt=getattr(response.prompt, "user_prompt", None) if response.prompt else None,
            system_prompt=getattr(response.prompt, "system_prompt", None) if response.prompt else None,
            lang_name=getattr(response.lang, "lang_name", None) if response.lang else None
        )
    except HTTPException:
        session.rollback()
        raise
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Error creating response: {str(e)}")
    finally:
        session.close()


@response_router.delete("/delete/{response_id}", summary="Delete a response by ID")
async def delete_response(
    response_id: int, 
    db: DB = Depends(_get_db),
    authorization: Optional[str] = Header(None)
):
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header missing")

    session = db.Session()
    try:
        response = session.query(ResponsesTable).filter(ResponsesTable.response_id == response_id).first()
        if not response:
            raise HTTPException(status_code=404, detail="Response not found")
        
        # Store response_id for logging before deletion
        response_id_str = str(response.response_id)
        response_text_preview = response.response_text[:50] if response.response_text else ""
        
        session.delete(response)
        session.commit()
        
        # Log the activity
        username = get_username_from_token(authorization)
        if username:
            log_activity(
                username=username,
                entity_type="Response",
                entity_id=response_id_str,
                operation="delete",
                note=f"Response '{response_id_str}' deleted: {response_text_preview}..."
            )
        
        return JSONResponse(content={"message": "Response deleted successfully"}, status_code=200)
    except HTTPException:
        session.rollback()
        raise
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Error deleting response: {str(e)}")
    finally:
        session.close()
