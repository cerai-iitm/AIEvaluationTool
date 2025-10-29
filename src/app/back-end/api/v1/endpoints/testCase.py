from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
import os
import sys

# Ensure the project 'src' directory is on sys.path so we can import lib.orm
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../../")))

from lib.orm.DB import DB

AIEVAL_DB_URL='mariadb+mariadbconnector://root:password@localhost:3306/test'
testcase_router = APIRouter(prefix="/api/testcases")

_db_instance: DB | None = None


def _get_db() -> DB:
    """Create or return a cached DB instance. Reads AIEVAL_DB_URL from env."""
    global _db_instance
    if _db_instance is not None:
        return _db_instance
    # db_url = os.getenv("AIEVAL_DB_URL")
    db_url =AIEVAL_DB_URL
    if not db_url:
        raise HTTPException(status_code=500, detail="Database URL not configured (AIEVAL_DB_URL)")
    _db_instance = DB(db_url=db_url, debug=False)
    return _db_instance
#---------------------------------------------------
# db: DB = _get_db()
db = DB(db_url=AIEVAL_DB_URL, debug=False)

@testcase_router.get("/t", summary="Get a test case")
async def list_testcase():
    testcase_response = db.testcases
    
    items = []
    
    for tc in testcase_response:
        # tc_id = getattr(tc, "testcase_id", None) or getattr(tc, "id", None)
        # tc_name = tc.name,
        # strategy_name = tc.strategy if tc.strategy else None
        # user_prompt = tc.prompt.user_prompt if tc.prompt else None
        # system_prompt = getattr(tc, "system_prompt", None)
        # response_text = getattr(tc, "response_text", None)
        # prompt = getattr(tc, "prompt", None)
        # response = getattr(tc, "response", None)
        
        items.append({
            "id": tc.testcase_id if tc.testcase_id else None,
            "testcase_name": tc.name if tc.name else None,
            "strategy_name": tc.strategy if tc.strategy else None,
            "user_prompt": tc.prompt.user_prompt if tc.prompt else None,
            "system_prompt": tc.prompt.system_prompt if tc.prompt else None,
            "response_text": tc.response.response_text if tc.response else None,
            "prompt": tc.judge_prompt.prompt if tc.judge_prompt else None,
            "domain": tc.prompt.kwargs.domain_id if tc.prompt.kwargs else None
        })
    
    return JSONResponse(content={"items": items})


#---------------------------------------------------

@testcase_router.get("/", summary="List test cases (paginated)")
async def list_testcases(db: DB = Depends(_get_db)):
    """

    Response shape:
    {
      "items": [ {"id": 1, "testcase_name": "P710", "strategy_name": "...", "domain_name": "..."}, ... ]
    }
    """
    try:
        # if page < 1 or page_size < 1:
        #     raise HTTPException(status_code=400, detail="page and page_size must be positive integers")
        db = _get_db()
        all_tcs = db.testcases

        # simple pagination
        # start = (page - 1) * page_size
        # end = start + page_size
        # sliced = all_tcs[start:end]

        items = []
        for tc in all_tcs:
            
            # tc is a data TestCase object created in DB layer; adapt field names defensively
            # tc_id = getattr(tc, "testcase_id", None) or getattr(tc, "id", None)
            tc_name = getattr(tc, "name")
            # strategy_name = getattr(tc, "strategy", None)
            # user_prompt = getattr(tc, "user_prompt", None)
            # system_prompt = getattr(tc, "system_prompt", None)
            # response_text = getattr(tc, "response_text", None)
            # prompt = getattr(tc, "prompt", None)
            # # domain may be on prompt.domain_id
            # domain_name = None
            prompt = getattr(tc, "prompt", None)
            if prompt is not None:
                domain_id = getattr(prompt, "domain_id", None)
                if domain_id is not None:
                    domain_name = db.get_domain_name(domain_id)

            items.append({
                # "id": tc_id,
                "testcase_name": tc_name,
                # "strategy_name": strategy_name,
                # "domain_name": domain_name or "Unknown",
                # "user_prompt": user_prompt,
                # "system_prompt": system_prompt,
                # "response_text": response_text,
                # "llm_prompt": prompt,
            })

        return JSONResponse({"items": items}, status_code=200)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
