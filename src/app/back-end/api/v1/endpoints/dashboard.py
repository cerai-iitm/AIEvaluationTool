from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
import os
import sys

# Ensure the project 'src' directory is on sys.path so we can import lib.orm
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../../")))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../database")))

from lib.orm.DB import DB
from lib.orm.tables import (
    Prompts,
    Responses,
    LLMJudgePrompts,
    Domains,
    Languages,
    Targets,
    TestCases,
    Strategies,
)
from database.fastapi_deps import get_db
# from config.settings import Settings
dashboard_router = APIRouter(prefix="/api/dashboard")

 


@dashboard_router.get("/summary", summary="Dashboard summary counts", tags=["Dashboard"])
async def get_dashboard_summary( db: DB = Depends(get_db)):
    try:
        db = get_db()

        # Use DB helpers where available
        test_cases_count = len(db.testcases) if db.testcases else 0
        targets_count = len(db.targets) if db.targets else 0
        domains_count = len(db.domains) if db.domains else 0
        strategies_count = len(db.strategies) if db.strategies else 0
        languages_count = len(db.languages) if db.languages else 0
        # responses_count = len
        # prompts_count = len(db.testcases.prompt)
        # llm_prompts_count = len(db.llm_judge_prompts) if db.llm_judge_prompts else 0

        # For prompts/responses/llm_prompts, count directly via session
        with db.Session() as session:
            prompts_count = session.query(Prompts).count()
            responses_count = session.query(Responses).count()
            llm_prompts_count = session.query(LLMJudgePrompts).count()
            # domains_count = session.query(Domains).count()
            # languages_count = session.query(Languages).count()
            # targets_count = session.query(Targets).count()
            # test_cases_count = session.query(TestCases).count()
            # strategies_count = session.query(Strategies).count()

        return JSONResponse({
            "test_cases": test_cases_count,
            "targets": targets_count,
            "domains": domains_count,
            "strategies": strategies_count,
            "languages": languages_count,
            "responses": responses_count,
            "prompts": prompts_count,
            "llm_prompts": llm_prompts_count,
        }, status_code=200)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
