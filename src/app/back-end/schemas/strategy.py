from pydantic import BaseModel
from typing import Optional

class StrategyIds(BaseModel):
    strategy_id : Optional[int]
    strategy_name : Optional[str]
    requires_llm_prompt : Optional[bool]

    
class Strategies(BaseModel):
    strategy_id : Optional[int]
    strategy_name : Optional[str]
    strategy_description : Optional[str]
    requires_llm_prompt : Optional[bool]


class StrategyCreate(BaseModel):
    strategy_name: str
    strategy_description: Optional[str] = None

class StrategyUpdate(BaseModel):
    strategy_name: Optional[str] = None
    strategy_description: Optional[str] = None