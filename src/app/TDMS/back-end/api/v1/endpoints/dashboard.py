from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
import os
import sys
from database.fastapi_deps import _get_db

# Ensure the project 'src' directory is on sys.path so we can import lib.orm
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../../../")))

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
    TestPlans,
    Metrics
)

# from config.settings import Settings
dashboard_router = APIRouter(prefix="/api/dashboard")

 


@dashboard_router.get("", summary="Dashboard summary counts", tags=["Dashboard"])
async def get_dashboard_summary(db: DB = Depends(_get_db)):
    session = db.Session()
    try:
        # Use DB helpers where available
        test_cases_count = session.query(TestCases).count()
        targets_count = session.query(Targets).count()
        domains_count = session.query(Domains).count()
        strategies_count = session.query(Strategies).count()
        languages_count = session.query(Languages).count()

        # For prompts/responses/llm_prompts, count directly via session
        
        prompts_count = session.query(Prompts).count()
        responses_count = session.query(Responses).count()
        llm_prompts_count = session.query(LLMJudgePrompts).count()
        test_plans_count = session.query(TestPlans).count()
        metrics_count = session.query(Metrics).count()

        return JSONResponse({
            "test_cases": test_cases_count,
            "targets": targets_count,
            "domains": domains_count,
            "strategies": strategies_count,
            "languages": languages_count,
            "responses": responses_count,
            "prompts": prompts_count,
            "llm_prompts": llm_prompts_count,
            "test_plans": test_plans_count,
            "metrics": metrics_count
        }, status_code=200)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        session.close()
