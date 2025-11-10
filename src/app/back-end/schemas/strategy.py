from pydantic import BaseModel
from typing import Optional

class StrategyIds(BaseModel):
    strategy_id : Optional[int]
    strategy_name : Optional[str]

    
class Strategies(BaseModel):
    strategy_id : Optional[int]
    strategy_name : Optional[str]
    strategy_description : Optional[str]