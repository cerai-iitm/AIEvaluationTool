from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
from schemas import StrategyIds, Strategies

import os
import sys

#Ensure the project 'src' directory is on sys.path so we can import lib.orm
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../../")))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../database")))

from lib.orm.DB import DB
from lib.orm.tables import Strategies as StrategiesTable
from database.fastapi_deps import _get_db

strategy_router = APIRouter(prefix="/api/strategies")


@strategy_router.get("/", response_model=list[StrategyIds])
async def list_strategies(db: DB = Depends(_get_db)):
    session = db.Session()
    try:
        strategies = session.query(StrategiesTable).all()
        return [
            StrategyIds(
                strategy_id=s.strategy_id,
                strategy_name=s.strategy_name,
            )
            for s in strategies
        ]
    finally:
        session.close()



@strategy_router.get("/all", response_model=list[Strategies])
async def get_strategies(db: DB = Depends(_get_db)):
    session = db.Session()
    try:
        strategies = session.query(StrategiesTable).all()
        return [
            Strategies(
                strategy_id=s.strategy_id,
                strategy_name=s.strategy_name,
                strategy_description=s.strategy_description,
            )
            for s in strategies
        ]
    finally:
        session.close()