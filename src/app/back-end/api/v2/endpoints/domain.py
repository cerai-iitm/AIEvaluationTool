from typing import List, Optional

from config.settings import settings
from database.fastapi_deps import _get_db
from fastapi import APIRouter, Depends, Header, HTTPException, status
from jose import JWTError, jwt
from schemas.domain import (
    DomainCreateV2,
    DomainDetailResponse,
    DomainListResponse,
    DomainUpdateV2,
    DomainBase,
)
from sqlalchemy.exc import IntegrityError
from utils.activity_logger import log_activity

from lib.orm.DB import DB
from lib.orm.tables import Domains

domain_router = APIRouter(prefix="/api/v2/domains")


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


@domain_router.get(
    "",
    response_model=List[DomainListResponse],
    summary="List all domains (v2)",
)
def list_domains(db: DB = Depends(_get_db)):
    try:
        domains = db.domains or []
        return [
            DomainListResponse(
                domain_id=d.code,  # assuming 'code' is the ID attribute; adjust if domain_id
                domain_name=d.name,
            )
            for d in domains
        ]
    except Exception as e:
        db.logger.error(f"Failed to fetch domains: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error fetching domains"
        )


# @domain_router.get(
#     "",
#     response_model=List[DomainListResponse],
#     summary="List all domains (v2)",
# )
# def list_domains(db: DB = Depends(_get_db)):
#     return db.list_domains_with_metadata() or []





# @domain_router.get(
#     "/{domain_id}",
#     response_model=DomainDetailResponse,
#     summary="Get a domain by ID (v2)",
# )
# def get_domain(domain_id: int, db: DB = Depends(_get_db)):
#     domain = db.get_domain_with_metadata(domain_id)
#     if domain is None:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND, detail="Domain not found"
#         )
#     return domain


@domain_router.post(
    "/create",
    response_model=DomainDetailResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new domain (v2)",
)
def create_domain(
    payload: DomainBase,
    db: DB = Depends(_get_db),
    authorization: Optional[str] = Header(None),
):
    # try:
    with db.Session() as session:
        try:
            existing_ids = [row[0] for row in session.query(Domains.domain_id).order_by(Domains.domain_id).all()]
            next_id = 1
            for id in existing_ids:
                if id != next_id:
                    break
                next_id += 1

            domain_obj = db._DB__add_or_get_domain_custom_Id(payload.domain_name, next_id)
            if domain_obj is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="A domain with the same name already exists.",
                )
            username = _get_username_from_token(authorization)
            if username:
                log_activity(
                    username=username,
                    entity_type="Domain",
                    entity_id=domain_obj.domain_id,
                    operation="create",
                    note=f"Domain {domain_obj.domain_name} created",
                )
            
            return DomainDetailResponse(
                domain_id=domain_obj.domain_id,
                domain_name=domain_obj.domain_name,
            )
        except IntegrityError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A domain with the same name already exists.",
            )
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        except Exception as e:
            db.logger.error(f"Failed to create domain: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal Server Error creating domain"
            )


@domain_router.get(
    "/{domain_id:int}",
    response_model=DomainDetailResponse,
    summary="Get a domain by ID (v2)",
)
def get_domain(domain_id: int, db: DB = Depends(_get_db)):
    domain_name = db.get_domain_name(domain_id)
    if domain_name is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Domain not found"
        )
    return DomainDetailResponse(domain_id=domain_id, domain_name=domain_name)


# @domain_router.post(
#     "/create",
#     response_model=DomainDetailResponse,
#     status_code=status.HTTP_201_CREATED,
#     summary="Create a new domain (v2)",
# )
# def create_domain(
#     payload: DomainCreateV2,
#     db: DB = Depends(_get_db),
#     authorization: Optional[str] = Header(None),
# ):
#     try:
#         domain_id = db.create_domain_v2(payload.model_dump())
#     except IntegrityError:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail="A domain with the same name already exists.",
#         )
#     except ValueError as e:
#         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

#     created = db.get_domain_with_metadata(domain_id)
#     if created is None:
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail="Domain created but could not be loaded.",
#         )

#     username = _get_username_from_token(authorization)
#     if username:
#         log_activity(
#             username=username,
#             entity_type="Domain",
#             entity_id=str(created["domain_name"]),
#             operation="create",
#             note=f"Domain '{created['domain_name']}' created (v2)",
#         )

#     return created


@domain_router.put(
    "/update/{domain_id:int}",
    response_model=DomainDetailResponse,
    summary="Update a domain (v2)",
)
def update_domain_v2(
    domain_id: int,
    payload: DomainUpdateV2,
    db: DB = Depends(_get_db),
    authorization: Optional[str] = Header(None),
):
    update_data = payload.model_dump(exclude_unset=True)
    if not update_data:
        existing_name = db.get_domain_name(domain_id)
        if existing_name is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Domain not found"
            )
        return DomainDetailResponse(
            domain_id=domain_id,
            domain_name=existing_name,
        )

    try:
        updated = db.update_domain_v2(domain_id, update_data)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        ) from exc

    if updated is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Domain not found"
        )

    username = _get_username_from_token(authorization)
    if username:
        log_activity(
            username=username,
            entity_type="Domain",
            entity_id=str(updated['domain_id']),
            operation="update",
            note="Domain name updated",
        )

    return DomainDetailResponse(
        domain_id=updated['domain_id'],
        domain_name=updated['domain_name'],
    )


@domain_router.delete(
    "/delete/{domain_id:int}",
    summary="Delete a domain (v2)",
)
def delete_domain(
    domain_id: int,
    db: DB = Depends(_get_db),
    authorization: Optional[str] = Header(None),
):
    existing = db.get_domain_name(domain_id)
    if existing is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Domain not found"
        )

    if not db.delete_domain_record(domain_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Domain not found"
        )

    username = _get_username_from_token(authorization)
    if username:
        log_activity(
            username=username,
            entity_type="Domain",
            entity_id=str(domain_id),
            operation="delete",
            note=f"Domain '{existing}' deleted",
        )

    return {"message": "Domain deleted successfully"}
