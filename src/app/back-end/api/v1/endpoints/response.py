from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
from schemas import Response
import os
import sys
from sqlalchemy.orm import joinedload

# Ensure the project 'src' directory is on sys.path so we can import lib.orm
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../../")))

from lib.orm.DB import DB
from lib.orm.tables import TestCases

AIEVAL_DB_URL='mariadb+mariadbconnector://root:password@localhost:3306/test'

response_router = APIRouter(prefix="/api/response")

_db_instance: DB | None = None


def _get_db() -> DB:
    """Create or return a cached DB instance. Reads AIEVAL_DB_URL from env."""
    global _db_instance
    if _db_instance is not None:
        return _db_instance
    # db_url = os.getenv("AIEVAL_DB_URL")
    db_url =AIEVAL_DB_URL
    if not db_url:
        raise HTTPException(status_code=500, detail="Database URL not configured (AIEVAL_DB_URL)")
    _db_instance = DB(db_url=db_url, debug=False)
    return _db_instance

db = DB(db_url=AIEVAL_DB_URL, debug=False)


@response_router.get("/", response_model=list[Response])
async def list_responses():
    pass

    # # response_list = db.get_response
    # response = db.testcases
    # # response = db.Session().query(TestCases).all()

    # items = []
    # for res in response:
    #     items.append({
    #         "id": res.response.response_id,
    #         "response_text": res.response.response_text,
            
    #     })


    # return JSONResponse(content={"items": items})
    # session = db.Session()

    # try:
    #     db_response = session.query(TestCases).options(joinedload(TestCases.response)).all()
    #     if not db_response:
    #         raise HTTPException(status_code = 404, detail="No response found")

    #     response_text = None
    #     if response_obj = getattr(db_response, "response", None):
    #     if response_obj is not None:
    #         response_text = getattr(response_obj, "response_text", None)

    #     items = []
    #     for response in db_response:
    #         items.append({
    #             "id": response.response.response_id,
    #             "response_text": response.response.response_text
    #         })