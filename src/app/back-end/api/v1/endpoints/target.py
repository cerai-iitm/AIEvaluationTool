from fastapi import APIRouter, HTTPException, Depends, Header
from fastapi.responses import JSONResponse
from schemas import User, Domain, Language
from schemas import TargetIds, TargetCreate, TargetUpdate

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

# Ensure the project 'src' directory is on sys.path so we can import lib.orm
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../../")))

from lib.orm.DB import DB
from lib.orm.tables import Targets, Domains, Languages

target_router = APIRouter(prefix="/api/targets")

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

from enum import Enum

class TargetTypeEnum(str, Enum):
    WhatsApp = "WhatsApp"
    WebApp = "WebApp"
    API = "API"


def get_current_user_info(current_user: user_model.Users = Depends(get_current_user)):
    """Get current authenticated user information."""
    return User(
        user_name=current_user.user_name,
        role=str(current_user.role)
    )

@target_router.get("/target/types", response_model=list[TargetTypeEnum], summary="Get all target types")
def get_target_types(db: DB = Depends(_get_db)):
    return list(TargetTypeEnum) 


@target_router.get("/domains", response_model=list[Domain], summary="Get all domains")
async def get_domains(db: DB = Depends(_get_db)):
    session = db.Session()
    try:
        domains = session.query(Domains).all()
        
        return [
            Domain(
                domain_id = domain.domain_id,
                domain_name = domain.domain_name
            ) 
            for domain in domains
        ]
    finally:
        session.close()


@target_router.get("/languages", response_model=list[Language], summary="Get all languages")
async def get_languages(db: DB = Depends(_get_db)):
    session = db.Session()
    try:
        languages = session.query(Languages).all()
        
        return [
            Domain(
                lang_id = lang.lang_id,
                lang_name = lang.lang_name
            ) 
            for lang in languages
        ]
    finally:
        session.close()


@target_router.get("", response_model=list[TargetIds], summary="Get all targets")
async def list_targets(db: DB = Depends(_get_db)):
    session = db.Session()
    try:
        targets = session.query(Targets).all()
        return [
            TargetIds(
                target_id=target.target_id,
                target_name=target.target_name,
                target_type=target.target_type,
                target_description=target.target_description,
                target_url=target.target_url,
                domain_name=target.domain.domain_name,
                lang_list=[lang.lang_name for lang in target.langs]
            )
            for target in targets
        ]
    finally:
        session.close()


@target_router.get("/{target_id}", response_model=TargetIds, summary="Get a target by ID")
async def get_target(target_id: int, db: DB = Depends(_get_db)):
    session = db.Session()
    try:
        target = session.query(Targets).filter(Targets.target_id == target_id).first()
        if target is None:
            raise HTTPException(status_code=404, detail="Target not found")
        return TargetIds(
            target_id=target.target_id,
            target_name=target.target_name,
            target_type=target.target_type,
            target_description=target.target_description,
            target_url=target.target_url,
            domain_name=target.domain.domain_name,
            lang_list=[lang.lang_name for lang in target.langs]
        )
    finally:
        session.close()


@target_router.put("/{target_id}", response_model=TargetIds, summary="Update a target by ID")
async def update_target(
    target_id: int,
    target_update: TargetUpdate,
    db: DB = Depends(_get_db),
    authorization: Optional[str] = Header(None)
):
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header missing")


    session = db.Session()
    try:
        target = session.query(Targets).filter(Targets.target_id == target_id).first()
        if target is None:
            raise HTTPException(status_code=404, detail="Target not found")

        # Validate URL uniqueness if provided
        if target_update.target_url:
            existing_url = (
                session.query(Targets)
                .filter(Targets.target_url == target_update.target_url, Targets.target_id != target_id)
                .first()
            )
            if existing_url:
                raise HTTPException(status_code=400, detail="Target URL already exists")
            target.target_url = target_update.target_url

        # Validate unique target name if provided
        if target_update.target_name:
            target.target_name = target_update.target_name

        if target_update.target_type:
            target.target_type = target_update.target_type

        if target_update.target_description is not None:
            target.target_description = target_update.target_description

        if target_update.domain_name:
            domain = session.query(Domains).filter(Domains.domain_name == target_update.domain_name).first()
            if domain is None:
                domain = Domains(domain_name=target_update.domain_name)
                session.add(domain)
                session.flush()
            target.domain = domain

        if target_update.lang_list is not None:
            updated_langs = []
            for lang_name in target_update.lang_list:
                lang = session.query(Languages).filter(Languages.lang_name == lang_name).first()
                if lang is None:
                    lang = Languages(lang_name=lang_name)
                    session.add(lang)
                    session.flush()
                updated_langs.append(lang)
            target.langs = updated_langs

        session.commit()
        session.refresh(target)

        username = get_username_from_token(authorization)
        if not username:
            raise HTTPException(status_code=401, detail="Invalid or expired token")
            
            changes = []
            if target.target_name is not None and target.target_name != target_update.target_name:
                changes.append(f"name changed from '{target.target_name}' to '{target_update.target_name}'")
            if target.target_type is not None and target.target_type != target_update.target_type:
                changes.append("type updated")
            if target.target_description is not None and target.target_description != target_update.target_description:
                changes.append("description updated")
            if target.domain_name is not None and target.domain_name != target_update.domain_name:
                changes.append("domain updated")
            if target.lang_list is not None and target.lang_list != target_update.lang_list:
                changes.append("languages updated")
            note = f"Target '{target.target_name}' updated"
            if changes:
                note += f": {', '.join(changes)}"
            else:
                note += " (no changes detected)"

            log_activity(
                username=username,
                entity_type="Target",
                entity_id=str(target.target_id),
                operation="update",
                note=f"Updated target '{target.target_name}'"
            )

        return TargetIds(
            target_id=target.target_id,
            target_name=target.target_name,
            target_type=target.target_type,
            target_description=target.target_description,
            target_url=target.target_url,
            domain_name=target.domain.domain_name if target.domain else None,
            lang_list=[lang.lang_name for lang in target.langs]
        )
    except HTTPException:
        session.rollback()
        raise
    except Exception as exc:
        session.rollback()
        raise HTTPException(status_code=500, detail=str(exc))
    finally:
        session.close()




@target_router.post("/create", response_model=TargetIds)
async def create_target(
    target_create: TargetCreate,
    db: DB = Depends(_get_db),
    authorization: Optional[str] = Header(None)
):
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header missing")

    session = db.Session()
    try:
        # Ensure target name is unique
        # existing_target = (
        #     session.query(Targets)
        #     .filter(Targets.target_name == target_create.target_name)
        #     .first()
        # )
        # if existing_target:
        #     raise HTTPException(status_code=400, detail="Target name already exists")

        # Ensure target URL is unique
        existing_url = (
            session.query(Targets)
            .filter(Targets.target_url == target_create.target_url)
            .first()
        )
        if existing_url:
            raise HTTPException(status_code=400, detail="Target URL already exists")

        domain = (
            session.query(Domains)
            .filter(Domains.domain_name == target_create.domain_name)
            .first()
        )
        if domain is None:
            domain = Domains(domain_name=target_create.domain_name)
            session.add(domain)
            session.flush()

        new_target = Targets(
            target_name=target_create.target_name,
            target_type=target_create.target_type,
            target_description=target_create.target_description,
            target_url=target_create.target_url,
            domain=domain
        )

        session.add(new_target)
        session.flush()  # Ensure target_id is generated

        langs = []
        for lang_name in target_create.lang_list:
            lang = session.query(Languages).filter(Languages.lang_name == lang_name).first()
            if lang is None:
                lang = Languages(lang_name=lang_name)
                session.add(lang)
                session.flush()
            langs.append(lang)
        new_target.langs = langs

        session.commit()
        session.refresh(new_target)

        username = get_username_from_token(authorization)
        if not username:
            raise HTTPException(status_code=401, detail="Invalid or expired token")

        log_activity(
            username=username,
            entity_type="Target",
            entity_id=str(new_target.target_id),
            operation="create",
            note=f"Created target '{new_target.target_name}'"
        )

        return TargetIds(
            target_id=new_target.target_id,
            target_name=new_target.target_name,
            target_type=new_target.target_type,
            target_description=new_target.target_description,
            target_url=new_target.target_url,
            domain_name=new_target.domain.domain_name if new_target.domain else None,
            lang_list=[lang.lang_name for lang in new_target.langs]
        )
    except HTTPException:
        session.rollback()
        raise
    except Exception as exc:
        session.rollback()
        raise HTTPException(status_code=500, detail=str(exc))
    finally:
        session.close()