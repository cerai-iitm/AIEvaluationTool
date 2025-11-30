from typing import List, Optional

from config.settings import settings
from database.fastapi_deps import _get_db
from fastapi import APIRouter, Depends, Header, HTTPException, status
from jose import JWTError, jwt
from schemas.strategy import (
    StrategyCreateV2,
    StrategyDetailResponse,
    StrategyListResponse,
    StrategyUpdateV2,
)
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from utils.activity_logger import log_activity

from lib.orm.DB import DB
from lib.orm.tables import TestCases, Strategies as StrategiesTable
from lib.data import Strategy

strategy_router = APIRouter(prefix="/api/v2/strategies")


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


@strategy_router.get(
    "",
    response_model=List[StrategyListResponse],
    summary="List all strategies (v2)",
)
def list_strategies(db: DB = Depends(_get_db)):
    strategy = db.strategies

    if strategy is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Strategies not found"
        )

    strategy_ids_with_llm_prompt = _get_strategy_ids_requiring_llm_prompt(db.Session())

    return [
        StrategyListResponse(
            strategy_id=strategy.strategy_id,
            strategy_name=strategy.name,
            requires_llm_prompt=strategy.strategy_id in strategy_ids_with_llm_prompt
        )
        for strategy in strategy
    ]


# @strategy_router.get(
#     "",
#     response_model=List[StrategyListResponse],
#     summary="List all strategies (v2)",
# )
# def list_strategies(db: DB = Depends(_get_db)):
#     return db.list_strategies_with_metadata() or []


@strategy_router.get(
    "/{strategy_id}",
    response_model=StrategyDetailResponse,
    summary="Get a strategy by ID (v2)",
)
def get_strategy(strategy_id: int, db: DB = Depends(_get_db)):
    strategy = db.get_strategy_id(strategy_id)

    if strategy is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Strategy not found"
        )

    strategy_ids_with_llm_prompt = _get_strategy_ids_requiring_llm_prompt(db.Session())    

    return StrategyDetailResponse(
        strategy_id=strategy.strategy_id,
        strategy_name=strategy.name,
        strategy_description=strategy.description,
        requires_llm_prompt=strategy.strategy_id in strategy_ids_with_llm_prompt

    )


# @strategy_router.get(
#     "/{strategy_id}",
#     response_model=StrategyDetailResponse,
#     summary="Get a strategy by ID (v2)",
# )
# def get_strategy(strategy_id: int, db: DB = Depends(_get_db)):
#     strategy = db.get_strategy_with_metadata(strategy_id)
#     if strategy is None:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND, detail="Strategy not found"
#         )
#     return strategy
# __add_or_get_strategy_custom_id



@strategy_router.post(
    "/create",
    response_model=StrategyDetailResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new strategy (v2)",
)
def create_strategy(
    payload: StrategyCreateV2,
    db: DB = Depends(_get_db),
    authorization: Optional[str] = Header(None),
):
    try:
        with db.Session() as session:
            existing_ids = [row[0] for row in session.query(StrategiesTable.strategy_id).order_by(StrategiesTable.strategy_id).all()]
            next_id = 1
            for id in existing_ids:
                if id != next_id:
                    break
                next_id += 1 

        strategy_data = Strategy( name=payload.strategy_name, description=payload.strategy_description)

        strategy_obj = db._DB__add_or_get_strategy_custom_id(strategy_data, next_id)
        if strategy_obj is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A strategy with the same name already exists.",
            )

        username = _get_username_from_token(authorization)
        if username:
            log_activity(
                username=username,
                entity_type="Strategy",
                entity_id=str(payload.strategy_name),
                operation="create",
                note=f"Created prompt with ID: {payload.strategy_name}",
            )

        return StrategyDetailResponse(
            strategy_id=strategy_obj.strategy_id,
            strategy_name=strategy_obj.strategy_name,
            strategy_description=strategy_obj.strategy_description
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    finally:
        db.Session.close()


    # try:
    #     strategy_id = db.create_strategy_v2(payload.model_dump())
    # except IntegrityError:
    #     raise HTTPException(
    #         status_code=status.HTTP_400_BAD_REQUEST,
    #         detail="A strategy with the same name already exists.",
    #     )
    # except ValueError as e:
    #     raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    # created = db.get_strategy_with_metadata(strategy_id)
    # if created is None:
    #     raise HTTPException(
    #         status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    #         detail="Strategy created but could not be loaded.",
    #     )

    # username = _get_username_from_token(authorization)
    # if username:
    #     log_activity(
    #         username=username,
    #         entity_type="Strategy",
    #         entity_id=str(created["strategy_name"]),
    #         operation="create",
    #         note=f"Strategy '{created['strategy_name']}' created (v2)",
    #     )

    # return created


@strategy_router.put(
    "/update/{strategy_id}",
    response_model=StrategyDetailResponse,
    summary="Update a strategy (v2)",
)
def update_strategy(
    strategy_id: int,
    payload: StrategyUpdateV2,
    db: DB = Depends(_get_db),
    authorization: Optional[str] = Header(None),
):
    update_data = payload.model_dump(exclude_unset=True)
    if not update_data:
        existing = db.get_strategy_id(strategy_id)
        if existing is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Strategy not found"
            )
        return existing

    try:
        updated = db.update_strategy_v2(strategy_id, update_data)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        ) from exc

    if updated is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Strategy not found"
        )

    username = _get_username_from_token(authorization)
    if username:
        log_activity(
            username=username,
            entity_type="Strategy",
            entity_id=str(updated["strategy_name"]),
            operation="update",
            note="Strategy updated via v2 endpoint",
        )

    return updated


@strategy_router.delete(
    "/delete/{strategy_id}",
    summary="Delete a strategy (v2)",
)
def delete_strategy(
    strategy_id: int,
    db: DB = Depends(_get_db),
    authorization: Optional[str] = Header(None),
):
    existing = db.get_strategy_id(strategy_id)
    if existing is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Strategy not found"
        )

    if not db.delete_strategy_record(strategy_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Strategy not found"
        )

    username = _get_username_from_token(authorization)
    if username:
        log_activity(
            username=username,
            entity_type="Strategy",
            entity_id=str(existing.name),
            operation="delete",
            note=f"Strategy '{existing.name}' deleted",
        )

    return {"message": "Strategy deleted successfully"}
