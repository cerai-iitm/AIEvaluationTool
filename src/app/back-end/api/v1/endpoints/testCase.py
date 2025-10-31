from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
from schemas import TestCase, TestCaseUpdate
import os
import sys

# Ensure the project 'src' directory is on sys.path so we can import lib.orm
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../../")))

from lib.orm.DB import DB
from lib.orm.tables import TestCases
from lib.orm.tables import Responses
from lib.data.response import Response
from lib.data.prompt import Prompt
from lib.data.llm_judge_prompt import LLMJudgePrompt
from sqlalchemy.orm import joinedload

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
    domain_name = db.domains
    
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

        domain_name = db.get_domain_name(tc.prompt.domain_id)
        
        # if domain_name is not None:
        #     domain_name = domain_name.domain_name
        # else:
        #     domain_name = "Unknown"

        items.append({
            "id": tc.testcase_id if tc.testcase_id else None,
            "testcase_name": tc.name if tc.name else None,
            "strategy_name": tc.strategy if tc.strategy else None,
            "user_prompt": tc.prompt.user_prompt if tc.prompt else None,
            "system_prompt": tc.prompt.system_prompt if tc.prompt else None,
            "response_text": tc.response.response_text if tc.response else None,
            "prompt": tc.judge_prompt.prompt if tc.judge_prompt else None,
            "domain": domain_name
        })
    
    return JSONResponse(content={"items": items})


@testcase_router.put("/t/{id}", summary="Update a test case by id")
async def update_testcase(id: int, testcase: TestCase):
    print(id)
    testcase_update = db.Session().query(TestCases).filter(TestCases.testcase_id == id).first()
    # testcase_sample = db.get_testcase_by_id(id)
    # print(testcase_sample)
    if not testcase_update:
        raise HTTPException(status_code=404, detail="Test case not found")

    testcase_update.name = testcase.testcase_name
    testcase_update.strategy.strategy_name = testcase.strategy_name
    # testcase_update.domain_name = testcase.domain_name
    testcase_update.prompt.user_prompt = testcase.user_prompt
    testcase_update.prompt.system_prompt = testcase.system_prompt
    testcase_update.response.response_text = testcase.response_text
    # testcase_update.judge_prompt.prompt = testcase.prompt if testcase.prompt else None
    if testcase_update.judge_prompt is not None:
        testcase_update.judge_prompt.prompt = testcase.prompt
    

    db.Session().commit()

    return JSONResponse(content={"message": "Test case updated successfully"})

#---------------------------------------------------
@testcase_router.get("/{testcase_id}", response_model=TestCase )
def get_testcase(testcase_id: int):
    session = db.Session()
    try:
        db_testcase = (
            session.query(TestCases)
            .options(
                joinedload(TestCases.response),
                joinedload(TestCases.prompt),
                joinedload(TestCases.strategy),
                joinedload(TestCases.judge_prompt),
            )
            .filter(TestCases.testcase_id == testcase_id)
            .first()
        )
        if not db_testcase:
            raise HTTPException(status_code=404, detail="Test case not found")

        # Collect related data while session is active
        strategy_name = None
        maybe_strategy = getattr(db_testcase, "strategy", None)
        if maybe_strategy is not None:
            strategy_name = getattr(maybe_strategy, "strategy_name", None)
            if strategy_name is None and isinstance(maybe_strategy, str):
                strategy_name = maybe_strategy

        user_prompt = None
        system_prompt = None
        domain_name = None
        prompt_obj = getattr(db_testcase, "prompt", None)
        if prompt_obj is not None:
            user_prompt = getattr(prompt_obj, "user_prompt", None)
            system_prompt = getattr(prompt_obj, "system_prompt", None)
            domain_id = getattr(prompt_obj, "domain_id", None)
            if domain_id is not None:
                domain_name = db.get_domain_name(domain_id)

        response_text = None
        response_obj = getattr(db_testcase, "response", None)
        if response_obj is not None:
            response_text = getattr(response_obj, "response_text", None)

        judge_prompt_text = None
        judge_prompt_obj = getattr(db_testcase, "judge_prompt", None)
        if judge_prompt_obj is not None:
            judge_prompt_text = getattr(judge_prompt_obj, "prompt", None)

        return TestCase(
            testcase_id=getattr(db_testcase, "testcase_id", None),
            testcase_name=getattr(db_testcase, "testcase_name", None),
            strategy_name=strategy_name,
            domain_name=domain_name,
            user_prompt=user_prompt,
            system_prompt=system_prompt,
            response_text=response_text,
            prompt=judge_prompt_text,
        )
    finally:
        session.close()


@testcase_router.put("/{testcase_id}", response_model=TestCaseUpdate)
async def update_testcase(testcase_id: int, testcase: TestCaseUpdate, db: DB = Depends(_get_db)):
    session = db.Session()
    try:
        db_testcase = (
            session.query(TestCases)
            .options(
                joinedload(TestCases.response),
                joinedload(TestCases.prompt),
                joinedload(TestCases.strategy),
                joinedload(TestCases.judge_prompt),
            )
            .filter(TestCases.testcase_id == testcase_id)
            .first()
        )
        if not db_testcase:
            raise HTTPException(status_code=404, detail="Test case not found")

        # Update strategy by name -> strategy_id
        if testcase.strategy_name is not None:
            current_strategy_name = (
                db_testcase.strategy.strategy_name if db_testcase.strategy else None
            )
            if testcase.strategy_name != current_strategy_name:
                new_strategy_id = db.add_or_get_strategy_id(testcase.strategy_name)
                if new_strategy_id == -1:
                    raise HTTPException(status_code=500, detail="Failed to add/get strategy")
                session.query(TestCases).filter(TestCases.testcase_id == testcase_id).update({TestCases.strategy_id: new_strategy_id}, synchronize_session=False)
                db_testcase.strategy_id = new_strategy_id

        # Update Prompt (user/system) -> prompt_id
        if testcase.user_prompt is not None or testcase.system_prompt is not None:
            existing_user = db_testcase.prompt.user_prompt if db_testcase.prompt else None
            existing_system = db_testcase.prompt.system_prompt if db_testcase.prompt else None
            new_user = testcase.user_prompt if testcase.user_prompt is not None else existing_user
            new_system = testcase.system_prompt if testcase.system_prompt is not None else existing_system
            if new_user != existing_user or new_system != existing_system:
                lang_id = getattr(db_testcase.prompt, "lang_id", None)
                domain_id = getattr(db_testcase.prompt, "domain_id", None)
                new_prompt = Prompt(system_prompt=new_system, user_prompt=new_user, lang_id=lang_id, domain_id=domain_id)
                new_prompt_id = db.add_or_get_prompt(new_prompt)
                if new_prompt_id == -1:
                    raise HTTPException(status_code=500, detail="Failed to add/get prompt")
                session.query(TestCases).filter(TestCases.testcase_id == testcase_id).update({TestCases.prompt_id: new_prompt_id}, synchronize_session=False)
                db_testcase.prompt_id = new_prompt_id

        # Update Response text -> response_id
        if testcase.response_text is not None:
            existing_resp_text = db_testcase.response.response_text if db_testcase.response else None
            if testcase.response_text != existing_resp_text:
                # Preserve response_type, language and existing prompt relation
                resp_type = (
                    getattr(db_testcase.response, "response_type", None) if db_testcase.response else None
                ) or "GT"
                prompt_id_for_resp = db_testcase.prompt_id
                lang_id = getattr(db_testcase.prompt, "lang_id", None)
                new_response = Response(
                    response_text=testcase.response_text,
                    response_type=resp_type,
                    prompt_id=prompt_id_for_resp,
                    lang_id=lang_id,
                )
                new_response_id = db.add_or_get_response(new_response, prompt_id_for_resp)
                if new_response_id == -1:
                    raise HTTPException(status_code=500, detail="Failed to add/get response")
                session.query(TestCases).filter(TestCases.testcase_id == testcase_id).update({TestCases.response_id: new_response_id}, synchronize_session=False)
                db_testcase.response_id = new_response_id

        # Update judge prompt text -> judge_prompt_id
        if testcase.prompt is not None:
            existing_judge = db_testcase.judge_prompt.prompt if db_testcase.judge_prompt else None
            if testcase.prompt != existing_judge:
                jp = LLMJudgePrompt(prompt=testcase.prompt, lang_id=getattr(db_testcase.prompt, "lang_id", None))
                new_judge_id = db.add_or_get_judge_prompt(jp)
                if new_judge_id == -1:
                    raise HTTPException(status_code=500, detail="Failed to add/get judge prompt")
                session.query(TestCases).filter(TestCases.testcase_id == testcase_id).update({TestCases.judge_prompt_id: new_judge_id}, synchronize_session=False)
                db_testcase.judge_prompt_id = new_judge_id

        session.commit()
        # Re-load to ensure we return the latest persisted FK values
        latest = (
            session.query(TestCases)
            .filter(TestCases.testcase_id == testcase_id)
            .first()
        )
        return JSONResponse({
            "testcase_id": testcase_id,
            "strategy_name": testcase.strategy_name,
            "strategy_id": getattr(latest, "strategy_id", None),
            "prompt_id": getattr(latest, "prompt_id", None),
            "user_prompt": testcase.user_prompt,
            "system_prompt": testcase.system_prompt,
            "response_text": testcase.response_text,
            "response_id": db_testcase.response_id,
            "judge_prompt": testcase.prompt,
            "judge_prompt_id": db_testcase.judge_prompt_id,
        }, status_code=200)
    finally:
        session.close()


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
