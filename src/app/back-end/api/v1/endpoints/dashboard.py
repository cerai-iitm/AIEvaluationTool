from fastapi import APIRouter, HTTPException
import os
import sys

# Ensure the project 'src' directory is on sys.path so we can import lib.orm
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../../")))

from lib.orm.DB import DB
from lib.orm.tables import (
    Prompts,
    Responses,
    LLMJudgePrompts,
)

dashboard_router = APIRouter(prefix="/api/dashboard")

_db_instance: DB | None = None


def _get_db() -> DB:
    global _db_instance
    if _db_instance is not None:
        return _db_instance
    db_url = os.getenv("AIEVAL_DB_URL")
    if not db_url:
        raise HTTPException(status_code=500, detail="Database URL not configured (AIEVAL_DB_URL)")
    # Debug disabled for production-style endpoint
    _db_instance = DB(db_url=db_url, debug=False)
    return _db_instance


@dashboard_router.get("/summary", summary="Dashboard summary counts", tags=["Dashboard"])
async def get_dashboard_summary():
    try:
        db = _get_db()

        # Use DB helpers where available
        test_cases_count = len(db.testcases) if db.testcases else 0
        targets_count = len(db.targets) if db.targets else 0
        domains_count = len(db.domains) if db.domains else 0
        strategies_count = len(db.strategies) if db.strategies else 0
        languages_count = len(db.languages) if db.languages else 0

        # For prompts/responses/llm_prompts, count directly via session
        with db.Session() as session:
            prompts_count = session.query(Prompts).count()
            responses_count = session.query(Responses).count()
            llm_prompts_count = session.query(LLMJudgePrompts).count()

        return {
            "test_cases": test_cases_count,
            "targets": targets_count,
            "domains": domains_count,
            "strategies": strategies_count,
            "languages": languages_count,
            "responses": responses_count,
            "prompts": prompts_count,
            "llm_prompts": llm_prompts_count,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
