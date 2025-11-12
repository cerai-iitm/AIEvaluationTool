from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session, joinedload
from schemas import StrategyIds, Strategies

import os
import sys

#Ensure the project 'src' directory is on sys.path so we can import lib.orm
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../../")))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../database")))

from lib.orm.DB import DB
from lib.orm.tables import TestCases, Strategies as StrategiesTable
from database.fastapi_deps import _get_db

strategy_router = APIRouter(prefix="/api/strategies")


def _get_strategy_ids_requiring_llm_prompt(session: Session) -> set[int]:
    return {
        strategy_id
        for (strategy_id,) in (
            session.query(TestCases.strategy_id)
            .filter(TestCases.judge_prompt_id.isnot(None))
            .distinct()
        )
        if strategy_id is not None
    }


@strategy_router.get("/", response_model=list[StrategyIds])
async def list_strategies(db: DB = Depends(_get_db)):
    session = db.Session()
    try:
        strategy_ids_with_llm_prompt = _get_strategy_ids_requiring_llm_prompt(session)

        strategies = session.query(StrategiesTable).all()
        return [
            StrategyIds(
                strategy_id=s.strategy_id,
                strategy_name=s.strategy_name,
                requires_llm_prompt=s.strategy_id in strategy_ids_with_llm_prompt,
            )
            for s in strategies
        ]
    finally:
        session.close()


@strategy_router.get("/all", response_model=list[Strategies])
async def get_strategies(db: DB = Depends(_get_db)):
    session = db.Session()
    try:
        strategy_ids_with_llm_prompt = _get_strategy_ids_requiring_llm_prompt(session)

        strategies = session.query(StrategiesTable).all()
        return [
            Strategies(
                strategy_id=s.strategy_id,
                strategy_name=s.strategy_name,
                strategy_description=s.strategy_description,
                requires_llm_prompt=s.strategy_id in strategy_ids_with_llm_prompt,
            )
            for s in strategies
        ]
    finally:
        session.close()
