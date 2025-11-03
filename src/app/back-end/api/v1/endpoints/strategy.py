from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse

import os
import sys

#Ensure the project 'src' directory is on sys.path so we can import lib.orm
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../../")))

from lib.orm.DB import DB
from lib.orm.tables import Strategies

AIEVAL_DB_URL='mariadb+mariadbconnector://root:password@localhost:3306/test'

strategy_router = APIRouter(prefix="/api/strategies")

_db_instance: DB | None = None

def _get_db() -> DB:
    global _db_instance
    if _db_instance is not None:
        return _db_instance
    db_url = AIEVAL_DB_URL
    if not db_url:
        raise HTTPException(status_code=500, detail="Database URL not configured (AIEVAL_DB_URL)")
    # Debug disabled for production-style endpoint
    _db_instance = DB(db_url=db_url, debug=False)
    return _db_instance


db = DB(db_url=AIEVAL_DB_URL, debug=False)

@strategy_router.get("/")
async def list_strategies():
# async def get_strategies(db: DB = Depends(_get_db)):
    # with db.Session() as session:
    #     strategies = session.query(Strategies).all()

    #     return strategies
    strategy_response = db.strategies 

    items = []
    for strategy in strategy_response:

        items.append({
            "id": strategy.strategy_id if strategy.strategy_id else None,
            "strategy_name": strategy.name if strategy.name else None
        })  

    return JSONResponse(content={"items": items})