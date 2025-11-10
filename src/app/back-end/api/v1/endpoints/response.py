from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
from schemas import Response, ResponseIds
import os
import sys
from sqlalchemy.orm import joinedload

# Ensure the project 'src' directory is on sys.path so we can import lib.orm
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../../")))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../database")))

from lib.orm.DB import DB
from lib.orm.tables import TestCases, Responses
from database.fastapi_deps import _get_db

response_router = APIRouter(prefix="/api/responses")


@response_router.get("/", response_model=list[ResponseIds])
async def list_responses(db: DB = Depends(_get_db)):
    session = db.Session()
    try:
        responses = session.query(Responses).all()
        return [
            ResponseIds(
                response_id=getattr(r, "response_id", None),
                response_text=getattr(r, "response_text", None),
            )
            for r in responses
        ]
    finally:
        session.close()
