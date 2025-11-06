from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
from schemas import TestCase, TestCaseUpdate
import os
import sys

# Ensure the project 'src' directory is on sys.path so we can import lib.orm
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../../")))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../database")))

from lib.orm.DB import DB
from lib.orm.tables import TestCases
from lib.orm.tables import Responses
from lib.data.response import Response
from lib.data.prompt import Prompt
from lib.data.llm_judge_prompt import LLMJudgePrompt
from sqlalchemy.orm import joinedload
from database.fastapi_deps import get_db

testcase_router = APIRouter(prefix="/api/testcases")

@testcase_router.get("/t", summary="Get a test case")
async def list_testcases( db: DB = Depends(get_db)):
    testcase_response = db.testcases
    domain_name = db.domains
    return JSONResponse(content={"testcases": [{"id": tc.testcase_id, "name": tc.name, "prompt": tc.prompt.name, "domain": domain_name} for tc in testcase_response]})

@testcase_router.put("/t/{id}", summary="Update a test case by id")
async def update_testcase(id: int, testcase: TestCase, db: DB = Depends(get_db)):
    print(id)
    testcase_update = db.Session().query(TestCases).filter(TestCases.testcase_id == id).first()
    if not testcase_update:
        raise HTTPException(status_code=404, detail="Test case not found")
    testcase_update.name = testcase.name
    testcase_update.prompt_id = testcase.prompt_id
    db.Session().commit()
    return JSONResponse(content={"message": "Test case updated successfully"})

@testcase_router.get("/{testcase_id}", response_model=TestCase )
def get_testcase(testcase_id: int, db: DB = Depends(get_db)):
    session = db.Session()
    tc = session.query(TestCases).filter(TestCases.testcase_id == testcase_id).first()
    if not tc:
        raise HTTPException(status_code=404, detail="Test case not found")
    domain_name = db.get_domain_name(tc.prompt.domain_id)
    return {"id": tc.testcase_id, "name": tc.name, "prompt": tc.prompt.name, "domain": domain_name}

@testcase_router.put("/{testcase_id}", response_model=TestCaseUpdate)
async def update_testcase(testcase_id: int, testcase: TestCaseUpdate, db: DB = Depends(get_db)):
    session = db.Session()
    tc = session.query(TestCases).filter(TestCases.testcase_id == testcase_id).first()
    if not tc:
        raise HTTPException(status_code=404, detail="Test case not found")
    tc.name = testcase.name
    tc.prompt_id = testcase.prompt_id
    db.Session().commit()
    return {"message": "Test case updated successfully"}

@testcase_router.get("/", summary="List test cases (paginated)")
async def list_testcases(db: DB = Depends(get_db)):
    all_tcs = db.testcases
    return JSONResponse(content={"testcases": [{"id": tc.testcase_id, "name": tc.name, "prompt": tc.prompt.name, "domain": db.get_domain_name(tc.prompt.domain_id)} for tc in all_tcs]})
