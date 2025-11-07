from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
from schemas import TestCaseIds, TestCaseUpdate, TestCaseCreate
from database.fastapi_deps import _get_db
import os
import sys

# Ensure the project 'src' directory is on sys.path so we can import lib.orm
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../../")))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../database")))

from lib.orm.DB import DB
from lib.orm.tables import TestCases
from sqlalchemy.orm import joinedload


testcase_router = APIRouter(prefix="/api/testcases")

@testcase_router.get("/", summary="Get a test cases", response_model=list[TestCaseIds])
async def list_testcases( db: DB = Depends(_get_db)):
    session = db.Session()
    try:
        testcases = session.query(TestCases).all()
        return [
            TestCaseIds(
                testcase_id = tc.testcase_id,
                testcase_name = tc.testcase_name,
                strategy_name = tc.strategy.strategy_name,
                llm_judge_prompt = tc.judge_prompt.prompt if tc.judge_prompt else None,
                domain_name = tc.prompt.domain.domain_name if tc.prompt.domain else None,
                user_prompt = tc.prompt.user_prompt if tc.prompt else None,
                system_prompt = tc.prompt.system_prompt if tc.prompt else None,
                response_text = tc.response.response_text if tc.response else None
            )
            for tc in testcases
        
        ]
    finally:
        session.close()
    # testcase_response = db.testcases
    # domain_name = db.domains
    # return JSONResponse(content={"testcases": [{"id": tc.testcase_id, "name": tc.name, "prompt": tc.prompt.name, "domain": domain_name} for tc in testcase_response]})

# @testcase_router.put("/t/{id}", summary="Update a test case by id")
# async def update_testcase(id: int, testcase: TestCase, db: DB = Depends(_get_db)):
#     print(id)
#     testcase_update = db.Session().query(TestCases).filter(TestCases.testcase_id == id).first()
#     if not testcase_update:
#         raise HTTPException(status_code=404, detail="Test case not found")
#     testcase_update.name = testcase.name
#     testcase_update.prompt_id = testcase.prompt_id
#     db.Session().commit()
#     return JSONResponse(content={"message": "Test case updated successfully"})

@testcase_router.get("/{testcase_id}", response_model=TestCaseIds)
def get_testcase(testcase_id: int, db: DB = Depends(_get_db)):
    session = db.Session()
    try:
        tc = session.query(TestCases).filter(TestCases.testcase_id == testcase_id).first()
        if not tc:
            raise HTTPException(status_code=404, detail="Test case not found")
        return TestCaseIds(
            testcase_id = tc.testcase_id,
            testcase_name = tc.testcase_name,
            strategy_name = tc.strategy.strategy_name,
            llm_judge_prompt = tc.judge_prompt.prompt if tc.judge_prompt else None,
            domain_name = tc.prompt.domain.domain_name if tc.prompt.domain else None,
            user_prompt = tc.prompt.user_prompt if tc.prompt else None,
            system_prompt = tc.prompt.system_prompt if tc.prompt else None,
            response_text = tc.response.response_text if tc.response else None
        )
    finally:
        session.close()
    # session = db.Session()
    # tc = session.query(TestCases).filter(TestCases.testcase_id == testcase_id).first()
    # if not tc:
    #     raise HTTPException(status_code=404, detail="Test case not found")
    # domain_name = db.get_domain_name(tc.prompt.domain_id)
    # return {"id": tc.testcase_id, "name": tc.name, "prompt": tc.prompt.name, "domain": domain_name}

@testcase_router.put("/{testcase_id}", response_model=TestCaseUpdate)
async def update_testcase(testcase_id: int, testcase: TestCaseUpdate, db: DB = Depends(_get_db)):
    session = db.Session()
    try:
        tc = session.query(TestCases).filter(TestCases.testcase_id == testcase_id).first()
        if not tc:
            raise HTTPException(status_code=404, detail="Test case not found")
        
        tc.prompt_id = testcase.prompt_id
        tc.strategy_id = testcase.strategy_id
        tc.judge_prompt_id = testcase.llm_judge_prompt if testcase.llm_judge_prompt else None
        tc.prompt_id = testcase.prompt_id
        tc.response_id = testcase.response_id
        db.Session().commit()
        return TestCaseIds(
            testcase_id=tc.testcase_id, 
            testcase_name=tc.testcase_name, 
            strategy_id=tc.strategy_id,
            strategy_name=tc.strategy.strategy_name, 
            llm_judge_prompt_id=tc.judge_prompt_id,
            llm_judge_prompt=tc.judge_prompt.prompt if tc.judge_prompt else None, 
            domain_name=tc.prompt.domain.domain_name if tc.prompt.domain else None, 
            prompt_id=tc.prompt_id,
            user_prompt=tc.prompt.user_prompt if tc.prompt else None, 
            system_prompt=tc.prompt.system_prompt if tc.prompt else None, 
            response_id=tc.response_id,
            response_text=tc.response.response_text if tc.response else None
            )
    finally:
        session.close()


@testcase_router.post("/create", response_model=TestCaseIds)
async def create_testcase(testcase: TestCaseCreate, db: DB = Depends(_get_db)):
    session = db.Session()
    try:
        tc = TestCases(
            testcase_name=testcase.testcase_name, # whic is not equal to the testcase_name in the database
            strategy_id=testcase.strategy_id,
            judge_prompt_id=testcase.llm_judge_prompt if testcase.llm_judge_prompt else None, 
            prompt_id=testcase.prompt_id ,
            response_id=testcase.response_id
            )

        session.add(tc)
        session.commit()
        return TestCaseIds(
            testcase_id=tc.testcase_id, 
            testcase_name=tc.testcase_name, 
            strategy_name=tc.strategy.strategy_name, 
            llm_judge_prompt=tc.judge_prompt.prompt if tc.judge_prompt else None, 
            domain_name=tc.prompt.domain.domain_name if tc.prompt.domain else None, 
            user_prompt=tc.prompt.user_prompt if tc.prompt else None, 
            system_prompt=tc.prompt.system_prompt if tc.prompt else None, 
            response_text=tc.response.response_text if tc.response else None
            )
    finally:
        session.close()


@testcase_router.delete("/{testcase_id}")
async def delete_testcase(testcase_id: int, db: DB = Depends(_get_db)):
    session = db.Session()
    try:
        tc = session.query(TestCases).filter(TestCases.testcase_id == testcase_id).first()
        if not tc:
            raise HTTPException(status_code=404, detail="Test case not found")
        session.delete(tc)
        session.commit()
        return JSONResponse(content={"message": "Test case deleted successfully"}, status_code=200)
    finally:
        session.close()
