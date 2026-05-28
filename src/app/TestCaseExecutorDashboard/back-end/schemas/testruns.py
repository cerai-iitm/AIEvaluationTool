from pydantic import BaseModel
from typing import Optional,List

class TestRunResponse(BaseModel):
    run_id: int
    run_name: str
    target: str
    status: str
    start_ts: str
    end_ts: Optional[str]
    evaluation_ts: Optional[str]
    domain: Optional[str] 
    duration_ms: Optional[int] = None
    average_score: Optional[float] = None
    totalPages: Optional[int] = None
    analysis_status: str
    
class TestRunDetailsResponse(BaseModel):
    run_name: str
    testcase_name: str
    metric_name: str
    plan_name: str
    conversation_id: int
    status: str
    detail_id: int    
    score: Optional[float] = None
    evaluation_reason: Optional[str] = None  # ← add this

class TestRunSummaryResponse(BaseModel):
    run_id: int
    run_name: str
    target: Optional[str] = None
    domain: Optional[str] = None
    status: str
    start_ts: str
    end_ts: Optional[str] = None
    average_score: Optional[float] = None
    analysis_status: str = "failed"  # default status
    


class TestRunFullResponse(BaseModel):
    summary: TestRunSummaryResponse
    details: List[TestRunDetailsResponse]  

class EvaluationItemResponse(BaseModel):
    detail_id: int
    testcase: str
    agent_response: Optional[str]
    evaluation_score: Optional[int]
    evaluation_reason: Optional[str]
    evaluation_ts: Optional[str]


class RunEvaluationSummaryResponse(BaseModel):
    run: TestRunSummaryResponse
    evaluations: List[EvaluationItemResponse]

class NewTestRun(BaseModel):
    target: Optional[str] = None  # 👈 optional now
    testPlan: str          # ✅ NAME, not ID
    testCaseId: Optional[str] = None
    metric: str            # ✅ NAME
    metric: str
    maxTestCases: str
    domain: str
    language: str
    runName: Optional[str] = None

class ContinueRunRequest(BaseModel):
    run_name: str    