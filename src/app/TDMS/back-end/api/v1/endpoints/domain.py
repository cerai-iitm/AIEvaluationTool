from fastapi import APIRouter, HTTPException, Depends, Header, Response
from schemas import Domain, DomainCreate, DomainUpdate
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

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../../")))

from lib.orm.DB import DB
from lib.orm.tables import Domains

domain_router = APIRouter(prefix="/api/domains")

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


@domain_router.get("", response_model=list[Domain], summary="Get all domains")
async def list_domains(db: DB = Depends(_get_db)):
    session = db.Session()
    try:
        domains = session.query(Domains).all()
        return [
            Domain(
                domain_id=domain.domain_id,
                domain_name=domain.domain_name
            )
            for domain in domains
        ]
    finally:
        session.close()


@domain_router.get("/{domain_id}", response_model=Domain, summary="Get a domain by ID")
async def get_domain(domain_id: int, db: DB = Depends(_get_db)):
    session = db.Session()
    try:
        domain = session.query(Domains).filter(Domains.domain_id == domain_id).first()
        if domain is None:
            raise HTTPException(status_code=404, detail="Domain not found")
        return Domain(
            domain_id=domain.domain_id,
            domain_name=domain.domain_name
        )
    finally:
        session.close()


@domain_router.post("/create", response_model=Domain, summary="Create a new domain")
async def create_domain(
        domain: DomainCreate, 
        db: DB = Depends(_get_db), 
        authorization: Optional[str] = Header(None)
    ):
    session = db.Session()
    try:
        existing_domain = session.query(Domains).filter(Domains.domain_name == domain.domain_name).first()
        if existing_domain:
            raise HTTPException(status_code=400, detail="Domain already exists")

        # Find the lowest unused domain_id
        existing_ids = [row[0] for row in session.query(Domains.domain_id).order_by(Domains.domain_id).all()]
        next_id = 1
        for id in existing_ids:
            if id != next_id:
                break
            next_id += 1

        new_domain = Domains(
            domain_id=next_id,
            domain_name=domain.domain_name
        )
         
        session.add(new_domain)
        session.commit()
        session.refresh(new_domain)

        username = get_username_from_token(authorization)
        if username:
            log_activity(
                username=username,
                entity_type="Domain",
                entity_id=new_domain.domain_id,
                operation="create",
                note=f"Domain '{new_domain.domain_name}' created"
            )

        return Domain(
            domain_id=new_domain.domain_id,
            domain_name=new_domain.domain_name
        )
    finally:
        session.close()


@domain_router.put("/update/{domain_id}", response_model=Domain, summary="Update a domain by ID")
async def update_domain(
        domain_id: int, 
        domain: DomainUpdate, 
        db: DB = Depends(_get_db),
        authorization: Optional[str] = Header(None)
    ):
    session = db.Session()
    try:
        domain_to_update = session.query(Domains).filter(Domains.domain_id == domain_id).first()
        if domain_to_update is None:
            raise HTTPException(status_code=404, detail="Domain not found")

        original_name = domain_to_update.domain_name

        if domain_to_update.domain_name == domain.domain_name:
            # Optionally: return 204 No Content or a custom message
            return Response(status_code=204)

        domain_to_update.domain_name = domain.domain_name

        session.commit()
        session.refresh(domain_to_update)

        username = get_username_from_token(authorization)
        if username: 

            if domain.domain_name:
                note = f"Domain '{original_name}' updated to '{domain_to_update.domain_name}'"
            else:
                note = f"Domain with ID {domain_id} updated to '{domain_to_update.domain_name}'"
            log_activity(
                username=username,
                entity_type="Domain",
                entity_id=domain_id,
                operation="update",
                note=note
            )

        return Domain(
            domain_id=domain_to_update.domain_id,
            domain_name=domain_to_update.domain_name
        )
    finally:
        session.close()


@domain_router.delete("/delete/{domain_id}", summary="Delete a domain by ID")
async def delete_domain(
        domain_id: int, 
        db: DB = Depends(_get_db),
        authorization: Optional[str] = Header(None)
    ):
    session = db.Session()
    try:
        domain_to_delete = session.query(Domains).filter(Domains.domain_id == domain_id).first()
        if domain_to_delete is None:
            raise HTTPException(status_code=404, detail="Domain not found")
        session.delete(domain_to_delete)
        session.commit()

        username = get_username_from_token(authorization)

        if username:
            if domain_to_delete.domain_name:
                note = f"Domain '{domain_to_delete.domain_name}' deleted"
            else:
                note = f"Domain with ID {domain_id} deleted"

            log_activity(
                username=username,
                entity_type="Domain",
                entity_id=domain_id,
                operation="delete",
                note=f"Domain '{domain_to_delete.domain_name}' deleted"
            )

    finally:
        session.close()

