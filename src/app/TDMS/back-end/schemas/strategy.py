from typing import Optional

from pydantic import BaseModel, Field


class StrategyBase(BaseModel):
    strategy_name: str = Field(..., description="The name of the strategy.")
    strategy_description: Optional[str] = Field(
        None, description="The description of the strategy."
    )


class StrategyCreateV2(StrategyBase):
    notes: Optional[str] = Field(None, description="User notes for this operation.")


class StrategyUpdateV2(BaseModel):
    strategy_name: Optional[str] = Field(
        None, description="The new name of the strategy."
    )
    strategy_description: Optional[str] = Field(
        None, description="The new description of the strategy."
    )
    user_note: Optional[str] = Field(None, description="User notes for this operation.")


class StrategyListResponse(BaseModel):
    strategy_id: int
    strategy_name: str
    strategy_description: Optional[str]
    requires_llm_prompt: bool 


class StrategyDetailResponse(BaseModel):
    strategy_id: int
    strategy_name: str
    strategy_description: Optional[str]
    requires_llm_prompt: Optional[bool] = Field(
        False, description="Whether the strategy requires an LLM prompt."
    )

    class Config:
        from_attributes = True
