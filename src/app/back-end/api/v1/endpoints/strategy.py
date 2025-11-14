from fastapi import APIRouter, HTTPException, Depends, Header, Response
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session, joinedload
from schemas import StrategyIds, Strategies, StrategyCreate, StrategyUpdate
from database.fastapi_deps import _get_db
from database.database import get_current_user
from models import user as user_model
from utils.activity_logger import log_activity
from jose import jwt, JWTError
from config.settings import settings
from typing import Optional

import os
import sys

#Ensure the project 'src' directory is on sys.path so we can import lib.orm
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../../")))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../database")))

from lib.orm.DB import DB
from lib.orm.tables import TestCases, Strategies as StrategiesTable
from database.fastapi_deps import _get_db

strategy_router = APIRouter(prefix="/api/strategies")

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


@strategy_router.get("/{strategy_id}", response_model=Strategies, summary="Get a strategy by ID")
async def get_strategy(strategy_id: int, db: DB = Depends(_get_db)):
    session = db.Session()
    try:
        strategy = session.query(StrategiesTable).filter(StrategiesTable.strategy_id == strategy_id).first()
        if strategy is None:
            raise HTTPException(status_code=404, detail="Strategy not found")
        
        strategy_ids_with_llm_prompt = _get_strategy_ids_requiring_llm_prompt(session)
        
        return Strategies(
            strategy_id=strategy.strategy_id,
            strategy_name=strategy.strategy_name,
            strategy_description=strategy.strategy_description,
            requires_llm_prompt=strategy.strategy_id in strategy_ids_with_llm_prompt,
        )
    finally:
        session.close()


@strategy_router.post("/create", response_model=Strategies, summary="Create a new strategy")
async def create_strategy(
        strategy: StrategyCreate, 
        db: DB = Depends(_get_db), 
        authorization: Optional[str] = Header(None)
    ):
    session = db.Session()
    try:
        existing_strategy = session.query(StrategiesTable).filter(StrategiesTable.strategy_name == strategy.strategy_name).first()
        if existing_strategy:
            raise HTTPException(status_code=400, detail="Strategy already exists")

        # Find the lowest unused strategy_id
        existing_ids = [row[0] for row in session.query(StrategiesTable.strategy_id).order_by(StrategiesTable.strategy_id).all()]
        next_id = 1
        for id in existing_ids:
            if id != next_id:
                break
            next_id += 1

        new_strategy = StrategiesTable(
            strategy_id=next_id,
            strategy_name=strategy.strategy_name,
            strategy_description=strategy.strategy_description
        )
         
        session.add(new_strategy)
        session.commit()
        session.refresh(new_strategy)

        username = get_username_from_token(authorization)
        if username:
            log_activity(
                username=username,
                entity_type="Strategy",
                entity_id=new_strategy.strategy_id,
                operation="create",
                note=f"Strategy '{new_strategy.strategy_name}' created"
            )

        strategy_ids_with_llm_prompt = _get_strategy_ids_requiring_llm_prompt(session)
        
        return Strategies(
            strategy_id=new_strategy.strategy_id,
            strategy_name=new_strategy.strategy_name,
            strategy_description=new_strategy.strategy_description,
            requires_llm_prompt=new_strategy.strategy_id in strategy_ids_with_llm_prompt,
        )
    finally:
        session.close()


@strategy_router.put("/update/{strategy_id}", response_model=Strategies, summary="Update a strategy by ID")
async def update_strategy(
        strategy_id: int, 
        strategy: StrategyUpdate, 
        db: DB = Depends(_get_db),
        authorization: Optional[str] = Header(None)
    ):
    session = db.Session()
    try:
        strategy_to_update = session.query(StrategiesTable).filter(StrategiesTable.strategy_id == strategy_id).first()
        if strategy_to_update is None:
            raise HTTPException(status_code=404, detail="Strategy not found")

        original_name = strategy_to_update.strategy_name

        # Check if updating name would conflict with existing strategy
        if strategy.strategy_name and strategy.strategy_name != original_name:
            existing_strategy = session.query(StrategiesTable).filter(
                StrategiesTable.strategy_name == strategy.strategy_name
            ).first()
            if existing_strategy:
                raise HTTPException(status_code=400, detail="Strategy name already exists")

        # Update fields if provided
        if strategy.strategy_name is not None:
            strategy_to_update.strategy_name = strategy.strategy_name
        if strategy.strategy_description is not None:
            strategy_to_update.strategy_description = strategy.strategy_description

        # Check if nothing changed
        if (strategy.strategy_name is None or strategy.strategy_name == original_name) and \
           (strategy.strategy_description is None or strategy.strategy_description == strategy_to_update.strategy_description):
            strategy_ids_with_llm_prompt = _get_strategy_ids_requiring_llm_prompt(session)
            return Strategies(
                strategy_id=strategy_to_update.strategy_id,
                strategy_name=strategy_to_update.strategy_name,
                strategy_description=strategy_to_update.strategy_description,
                requires_llm_prompt=strategy_to_update.strategy_id in strategy_ids_with_llm_prompt,
            )

        session.commit()
        session.refresh(strategy_to_update)

        username = get_username_from_token(authorization)
        if username: 
            note = f"Strategy '{original_name}' updated"
            if strategy.strategy_name and strategy.strategy_name != original_name:
                note = f"Strategy '{original_name}' updated to '{strategy_to_update.strategy_name}'"
            
            log_activity(
                username=username,
                entity_type="Strategy",
                entity_id=strategy_id,
                operation="update",
                note=note
            )

        strategy_ids_with_llm_prompt = _get_strategy_ids_requiring_llm_prompt(session)
        
        return Strategies(
            strategy_id=strategy_to_update.strategy_id,
            strategy_name=strategy_to_update.strategy_name,
            strategy_description=strategy_to_update.strategy_description,
            requires_llm_prompt=strategy_to_update.strategy_id in strategy_ids_with_llm_prompt,
        )
    finally:
        session.close()


@strategy_router.delete("/delete/{strategy_id}", summary="Delete a strategy by ID")
async def delete_strategy(
        strategy_id: int, 
        db: DB = Depends(_get_db),
        authorization: Optional[str] = Header(None)
    ):
    session = db.Session()
    try:
        strategy_to_delete = session.query(StrategiesTable).filter(StrategiesTable.strategy_id == strategy_id).first()
        if strategy_to_delete is None:
            raise HTTPException(status_code=404, detail="Strategy not found")
        
        strategy_name = strategy_to_delete.strategy_name
        session.delete(strategy_to_delete)
        session.commit()

        username = get_username_from_token(authorization)

        if username:
            note = f"Strategy '{strategy_name}' deleted" if strategy_name else f"Strategy with ID {strategy_id} deleted"

            log_activity(
                username=username,
                entity_type="Strategy",
                entity_id=strategy_id,
                operation="delete",
                note=note
            )

    finally:
        session.close()
