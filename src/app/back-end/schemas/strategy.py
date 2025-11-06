from pydantic import BaseModel
from typing import Optional

class StrategyIds(BaseModel):
    strategy_id : Optional[int]
    strategy_name : Optional[str]

    