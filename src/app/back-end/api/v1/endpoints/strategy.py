from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
from schemas import StrategyIds

import os
import sys

#Ensure the project 'src' directory is on sys.path so we can import lib.orm
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../../")))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../database")))

from lib.orm.DB import DB
from lib.orm.tables import Strategies
from database.fastapi_deps import get_db

strategy_router = APIRouter(prefix="/api/strategies")


@strategy_router.get("/", response_model=list[StrategyIds])
async def list_strategies(db: DB = Depends(get_db)):
    session = db.Session()
    try:
        strategies = session.query(Strategies).all()
        return [
            StrategyIds(
                strategy_id=getattr(s, "strategy_id", None),
                strategy_name=getattr(s, "strategy_name", None),
            )
            for s in strategies
        ]
    finally:
        session.close()
