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
from database.fastapi_deps import _get_db
# from config.settings import Settings
dashboard_router = APIRouter(prefix="/api/dashboard")

 


@dashboard_router.get("", summary="Dashboard summary counts", tags=["Dashboard"])
async def get_dashboard_summary(db: DB = Depends(_get_db)):
    session = db.Session()
    try:
        # Use DB helpers where available
        test_cases_count = len(db.testcases) if db.testcases else 0
        targets_count = len(db.targets) if db.targets else 0
        domains_count = len(db.domains) if db.domains else 0
        strategies_count = len(db.strategies) if db.strategies else 0
        languages_count = len(db.languages) if db.languages else 0

        # For prompts/responses/llm_prompts, count directly via session
        
        prompts_count = session.query(Prompts).count()
        responses_count = session.query(Responses).count()
        llm_prompts_count = session.query(LLMJudgePrompts).count()

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
    finally:
        session.close()
