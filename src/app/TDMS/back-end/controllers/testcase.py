# from sqlalchemy.orm import Session
# from schemas import TestCaseIds
# from config import helpers
# from fastapi import HTTPException   


# def create_testcase(db: Session, testcase: TestCaseIds):
#     try:
#         tc = TestCases(
#             testcase_name=testcase.testcase_name,
#             strategy_id=testcase.strategy_id,
#             judge_prompt_id=testcase.llm_judge_prompt, 
#             prompt_id=testcase.prompt_id,
#             response_id=testcase.response_id
#             )
#         db.add(tc)
#         db.commit()
#         db.refresh(tc)
#         return tc
#     except Exception as e:
#         raise HTTPException(status_code=400, detail=str(e))
#     return TestCaseIds(
#         testcase_id=tc.testcase_id, 
#         testcase_name=tc.testcase_name, 
#         strategy_name=tc.strategy.strategy_name, 
#         llm_judge_prompt=tc.judge_prompt.prompt if tc.judge_prompt else None, 
#         domain_name=tc.prompt.domain.domain_name if tc.prompt.domain else None, 
#         user_prompt=tc.prompt.user_prompt if tc.prompt else None, 
#         system_prompt=tc.prompt.system_prompt if tc.prompt else None, 
#         response_text=tc.response.response_text if tc.response else None
#         )


# def get_testcase(db: Session, testcase_id: int):
#     try:
#         return db.query(TestCases).filter(TestCases.testcase_id == testcase_id).first()
#     except Exception as e:
#         raise HTTPException(status_code=400, detail=str(e))


# def get_testcase_by_name(db: Session, testcase_name: str):
#     try:
#         return db.query(TestCases).filter(TestCases.name == testcase_name).first()
#     except Exception as e:
#         raise HTTPException(status_code=400, detail=str(e))


# def update_testcase(db: Session, testcase_id: int, testcase: TestCase):
#     try:
#         db.query(TestCases).filter(TestCases.testcase_id == testcase_id).update(testcase.dict())
#         db.commit()
#         return db.query(TestCases).filter(TestCases.testcase_id == testcase_id).first()
#     except Exception as e:
#         raise HTTPException(status_code=400, detail=str(e))