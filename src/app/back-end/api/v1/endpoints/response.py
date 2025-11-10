from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
from schemas import Response, ResponseIds, Responses
import os
import sys
from sqlalchemy.orm import joinedload

# Ensure the project 'src' directory is on sys.path so we can import lib.orm
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../../")))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../database")))

from lib.orm.DB import DB
from lib.orm.tables import TestCases, Responses as ResponsesTable
from database.fastapi_deps import _get_db

response_router = APIRouter(prefix="/api/responses")


@response_router.get("/", response_model=list[ResponseIds])
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



@response_router.get("/all", response_model=list[Responses])
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