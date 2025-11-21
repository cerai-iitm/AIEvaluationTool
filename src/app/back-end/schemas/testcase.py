from pydantic import BaseModel
from typing import Optional

class TestCaseIds(BaseModel):
    testcase_id: Optional[int] = None
    testcase_name: Optional[str] = None
    strategy_name: Optional[str] = None
    llm_judge_prompt: Optional[str] = None
    domain_name: Optional[str] = None
    user_prompt: Optional[str] = None
    system_prompt: Optional[str] = None
    response_text: Optional[str] = None
  
class TestCaseId(BaseModel):
    testcase_name: Optional[str] = None
    strategy_name: Optional[str] = None
    llm_judge_prompt: Optional[str] = None
    user_prompt: Optional[str] = None
    system_prompt: Optional[str] = None
    response_text: Optional[str] = None


class TestCaseUpdate(BaseModel):
    testcase_id : Optional[int] = None
    testcase_name: Optional[str] = None
    strategy_id: Optional[int] = None
    strategy_name: Optional[str] = None
    llm_judge_prompt_id: Optional[int] = None
    llm_judge_prompt: Optional[str] = None
    domain_name: Optional[str] = None
    prompt_id: Optional[int] = None
    user_prompt: Optional[str] = None
    system_prompt: Optional[str] = None
    response_id: Optional[int] = None
    response_text: Optional[str] = None
    
class TestCaseCreate(BaseModel):
    testcase_name: str
    strategy_name: str
    llm_judge_prompt: Optional[str] = None
    user_prompt: str
    system_prompt: Optional[str] = None
    response_text: Optional[str] = None


class TestCaseListResponse(BaseModel):
    testcase_id: int
    testcase_name: str
    user_prompt: Optional[str] = None
    system_prompt: Optional[str] = None
    response_text: Optional[str] = None
    strategy_name: Optional[str] = None
    llm_judge_prompt: Optional[str] = None
    domain_name: Optional[str] = None


class TestCaseDetailResponse(TestCaseListResponse):
    strategy_id: Optional[int] = None
    prompt_id: Optional[int] = None
    response_id: Optional[int] = None
    llm_judge_prompt_id: Optional[int] = None


class TestCaseCreateV2(BaseModel):
    testcase_name: str
    user_prompt: str
    system_prompt: Optional[str] = None
    response_text: Optional[str] = None
    strategy_name: str
    llm_judge_prompt: Optional[str] = None


class TestCaseUpdateV2(BaseModel):
    testcase_name: Optional[str] = None
    strategy_name: Optional[str] = None
    user_prompt: Optional[str] = None
    system_prompt: Optional[str] = None
    response_text: Optional[str] = None
    llm_judge_prompt: Optional[str] = None