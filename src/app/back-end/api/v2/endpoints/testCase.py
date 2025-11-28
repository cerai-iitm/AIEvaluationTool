from typing import List, Optional

from fastapi import APIRouter, Depends, Header, HTTPException, status
from jose import JWTError, jwt

from config.settings import settings
from database.fastapi_deps import _get_db
from lib.data.llm_judge_prompt import LLMJudgePrompt
from lib.data.prompt import Prompt
from lib.data.response import Response as ResponseData
from lib.data.test_case import TestCase as TestCaseModel
from lib.orm.DB import DB
from lib.orm.tables import TestCases, Prompts
from schemas import (
    TestCaseCreateV2,
    TestCaseDetailResponse,
    TestCaseListResponse,
    TestCaseUpdateV2,
)
from utils.activity_logger import log_activity
from sqlalchemy.orm import joinedload

testcase_router = APIRouter(prefix="/api/v2/testcases")


def _normalize_optional(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    normalized = value.strip()
    return normalized or None


def _get_username_from_token(authorization: Optional[str]) -> Optional[str]:
    if not authorization:
        return None
    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            return None
    except ValueError:
        return None

    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )
        return payload.get("user_name")
    except JWTError:
        return None


def _get_default_language_and_domain(db: DB) -> tuple[int, int]:
    languages = db.languages
    if not languages:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="No languages configured in the system.",
        )
    domains = db.domains
    if not domains:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="No domains configured in the system.",
        )
    return languages[0].code, domains[0].code


@testcase_router.get(
    "",
    response_model=List[TestCaseListResponse],
    summary="List all test cases (v2)",
)
def list_testcases(db: DB = Depends(_get_db)):
    testcases = db.testcases

    results = []
    for testcase in testcases:
        domain_name = db.get_domain_name(testcase.prompt.domain_id)
        response_str = (
            testcase.response.response_text
            if hasattr(testcase.response, "response_text")
            else str(testcase.response)
        )
        judge_prompt_str = (
            testcase.judge_prompt.prompt
            if hasattr(testcase.judge_prompt, "prompt")
            else str(testcase.judge_prompt)
        )
        results.append(
            TestCaseListResponse(
                testcase_id=testcase.testcase_id,
                testcase_name=testcase.name,
                user_prompt=testcase.prompt.user_prompt,
                system_prompt=testcase.prompt.system_prompt,
                response_text=response_str,
                strategy_name=testcase.strategy,
                llm_judge_prompt=judge_prompt_str,
                domain_name=domain_name,
            )
        )
    return results



# @testcase_router.get(
#     "",
#     response_model=List[TestCaseListResponse],
#     summary="List all test cases (v2)",
# )
# def list_testcases(db: DB = Depends(_get_db)):
    # return db.list_testcases_with_metadata() or []
    # return db.testcases

@testcase_router.get(
    "/{testcase_id}",
    response_model=TestCaseListResponse,
    summary="Get a test case by ID (v2)",
)
def get_testcase(testcase_id: int, db: DB = Depends(_get_db)):
    testcase = db.get_testcase_by_id(testcase_id)
    if testcase is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Test case not found")

    judge_prompt = testcase.judge_prompt
    llm_judge_prompt = judge_prompt.prompt if judge_prompt else None


    return TestCaseListResponse(
        testcase_id=testcase.testcase_id,
        testcase_name=testcase.name,
        user_prompt=testcase.prompt.user_prompt,
        system_prompt=testcase.prompt.system_prompt,
        response_text=testcase.response.response_text,
        strategy_name=testcase.strategy,
        llm_judge_prompt=llm_judge_prompt,
    )


# @testcase_router.get(
#     "/{testcase_id}",
#     response_model=TestCaseDetailResponse,
#     summary="Get a test case by ID (v2)",
# )
# def get_testcase(testcase_id: int, db: DB = Depends(_get_db)):
#     testcase = db.get_testcase_with_metadata(testcase_id)
#     if testcase is None:
#         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Test case not found")
#     return testcase

@testcase_router.post(
    "/create",
    response_model=TestCaseDetailResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new test case (v2)",
)
def create_testcase(
    payload: TestCaseCreateV2,
    db: DB = Depends(_get_db),
    authorization: Optional[str] = Header(None),
):
    try:
        # Get next available ID
        with db.Session() as session:
            existing_ids = [row[0] for row in session.query(TestCases.testcase_id).order_by(TestCases.testcase_id).all()]
            next_id = 1
            for id in existing_ids:
                if id != next_id:
                    break
                next_id += 1

        # Convert payload to TestCase model
        prompt = Prompt(
            user_prompt=payload.user_prompt.strip(),
            system_prompt=payload.system_prompt.strip() if payload.system_prompt else None,
            lang_id=1,  # Default language ID
            domain_id=1,  # Default domain ID
        )
        
        response = None
        if payload.response_text:
            response = Response(
                response_text=payload.response_text.strip(),
                response_type="GT",  # Ground Truth
                lang_id=1,  # Default language ID
            )
            
        judge_prompt = None
        if payload.llm_judge_prompt:
            judge_prompt = LLMJudgePrompt(
                prompt=payload.llm_judge_prompt.strip(),
                lang_id=1,  # Default language ID
            )
            
        testcase = TestCase(
            name=payload.testcase_name.strip(),
            prompt=prompt,
            response=response,
            judge_prompt=judge_prompt,
            strategy=payload.strategy_name.strip(),
            metric="exact_match"  # Default metric
        )
        
        # Add test case with custom ID
        testcase_obj = db._DB__add_or_get_test_case_custom_id(testcase, next_id)
        if not testcase_obj:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to create test case. It may already exist.",
            )
            
        # Log activity
        username = _get_username_from_token(authorization)
        if username:
            log_activity(
                username=username,
                entity_type="test_case",
                entity_id=str(testcase_obj.testcase_id),
                operation="create",
                note=f"Created test case: {testcase_obj.testcase_name}",
            )
            
        # Get the created test case with all relationships loaded
        with db.Session() as session:
            testcase_full = (
                session.query(TestCases)
                .options(
                    joinedload(TestCases.prompt),
                    joinedload(TestCases.response),
                    joinedload(TestCases.strategy),
                    joinedload(TestCases.judge_prompt),
                )
                .filter(TestCases.testcase_id == testcase_obj.testcase_id)
                .first()
            )
            
            if not testcase_full:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Test case not found after creation",
                )
                
            return TestCaseDetailResponse(
                testcase_id=testcase_full.testcase_id,
                testcase_name=testcase_full.testcase_name,
                user_prompt=testcase_full.prompt.user_prompt if testcase_full.prompt else None,
                system_prompt=testcase_full.prompt.system_prompt if testcase_full.prompt else None,
                response_text=testcase_full.response.response_text if testcase_full.response else None,
                strategy_name=testcase_full.strategy.strategy_name if testcase_full.strategy else None,
                llm_judge_prompt=testcase_full.judge_prompt.prompt if testcase_full.judge_prompt else None,
                domain_name=testcase_full.prompt.domain.domain_name if testcase_full.prompt and testcase_full.prompt.domain else None,
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while creating the test case: {str(e)}",
        )
    
# @testcase_router.post(
#     "/create",
#     response_model=TestCaseDetailResponse,
#     status_code=status.HTTP_201_CREATED,
#     summary="Create a new test case (v2)",
# )
# def create_testcase(
#     payload: TestCaseCreateV2,
#     db: DB = Depends(_get_db),
#     authorization: Optional[str] = Header(None),
# ):
#     lang_id, domain_id = _get_default_language_and_domain(db)
#     prompt = Prompt(
#         user_prompt=payload.user_prompt.strip(),
#         system_prompt=_normalize_optional(payload.system_prompt),
#         lang_id=lang_id,
#         domain_id=domain_id,
#     )

#     response_obj = None
#     normalized_response = _normalize_optional(payload.response_text)
#     if normalized_response:
#         response_obj = ResponseData(
#             response_text=normalized_response,
#             response_type="GT",
#             lang_id=lang_id,
#         )

#     judge_prompt_obj = None
#     normalized_judge_prompt = _normalize_optional(payload.llm_judge_prompt)
#     if normalized_judge_prompt:
#         judge_prompt_obj = LLMJudgePrompt(prompt=normalized_judge_prompt, lang_id=lang_id)

#     testcase_model = TestCaseModel(
#         name=payload.testcase_name.strip(),
#         metric="Unknown",
#         prompt=prompt,
#         response=response_obj,
#         strategy=payload.strategy_name.strip(),
#         judge_prompt=judge_prompt_obj,
#     )

#     testcase_id = db.add_testcase(testcase_model)
#     if testcase_id == -1:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail="A test case with the same configuration already exists.",
#         )

#     created = db.get_testcase_with_metadata(testcase_id)
#     if created is None:
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail="Test case created but could not be loaded.",
#         )

#     username = _get_username_from_token(authorization)
#     if username:
#         log_activity(
#             username=username,
#             entity_type="Test Case",
#             entity_id=str(created["testcase_name"]),
#             operation="create",
#             note=f"Test case '{created['testcase_name']}' created (v2)",
#         )

#     return created


@testcase_router.put(
    "/update/{testcase_id}",
    response_model=TestCaseDetailResponse,
    summary="Update a test case (v2)",
)
def update_testcase(
    testcase_id: int,
    payload: TestCaseUpdateV2,
    db: DB = Depends(_get_db),
    authorization: Optional[str] = Header(None),
):
    update_data = payload.model_dump(exclude_unset=True)

    normalized_updates: dict = {}
    for key, value in update_data.items():
        if isinstance(value, str):
            normalized_updates[key] = value.strip()
        else:
            normalized_updates[key] = value

    # Normalize optional fields
    for optional_field in ("system_prompt", "response_text", "llm_judge_prompt"):
        if optional_field in normalized_updates:
            normalized_updates[optional_field] = _normalize_optional(normalized_updates[optional_field])

    if not normalized_updates:
        # existing = db.get_testcase_with_metadata(testcase_id)
        # if existing is None:
        #     raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Test case not found")
        # return existing

        existing_testcase = db.get_testcase_by_id(testcase_id)
        if existing_testcase is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Test case not found")
        return existing_testcase

    try:
        updated = db.update_testcase_record(testcase_id, normalized_updates)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    if updated is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Test case not found")

    # Get the updated testcase with all relationships loaded
    with db.Session() as session:
        testcase = (
            session.query(TestCases)
            .options(
                joinedload(TestCases.prompt)
                .joinedload(Prompts.domain),
                joinedload(TestCases.strategy),
                joinedload(TestCases.response),
                joinedload(TestCases.judge_prompt),
            )
            .filter(TestCases.testcase_id == testcase_id)
            .first()
        )

        if testcase is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Test case not found after update")

        # Log activity if user is authenticated
        username = _get_username_from_token(authorization)
        if username:
            changes = []
            if "testcase_name" in normalized_updates:
                changes.append(f"name changed to '{testcase.testcase_name}'")
            if "user_prompt" in normalized_updates or "system_prompt" in normalized_updates:
                changes.append("prompt updated")
            if "response_text" in normalized_updates:
                changes.append("response updated")
            if "strategy_name" in normalized_updates:
                changes.append("strategy updated")
            if "llm_judge_prompt" in normalized_updates:
                changes.append("judge prompt updated")
            
            note = f"Test case '{testcase.testcase_name}' updated"
            if changes:
                note += f": {', '.join(changes)}"
            else:
                note += " (no changes detected)"
                
            log_activity(
                username=username,
                entity_type="Test Case",
                entity_id=str(testcase.testcase_id),
                operation="update",
                note=note,
            )

        # Build the response
        return {
            "testcase_id": testcase.testcase_id,
            "testcase_name": testcase.testcase_name,
            "strategy_id": testcase.strategy_id,
            "strategy_name": testcase.strategy.strategy_name if testcase.strategy else None,
            "llm_judge_prompt_id": testcase.judge_prompt_id,
            "llm_judge_prompt": testcase.judge_prompt.prompt if testcase.judge_prompt else None,
            "domain_id": testcase.prompt.domain_id if testcase.prompt else None,
            "domain_name": testcase.prompt.domain.domain_name if testcase.prompt and testcase.prompt.domain else None,
            "prompt_id": testcase.prompt_id,
            "user_prompt": testcase.prompt.user_prompt if testcase.prompt else None,
            "system_prompt": testcase.prompt.system_prompt if testcase.prompt else None,
            "response_id": testcase.response_id,
            "response_text": testcase.response.response_text if testcase.response else None,
        }


@testcase_router.delete(
    "/delete/{testcase_id}",
    summary="Delete a test case (v2)",
)
def delete_testcase(
    testcase_id: int,
    db: DB = Depends(_get_db),
    authorization: Optional[str] = Header(None),
):
    # existing = db.get_testcase_with_metadata(testcase_id)
    # if existing is None:
    #     raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Test case not found")
        
    existing = db.get_testcase_by_id(testcase_id)
    if existing is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Test case not found")
    

    if not db.delete_testcase_record(testcase_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Test case not found")

    username = _get_username_from_token(authorization)
    if username:
        log_activity(
            username=username,
            entity_type="Test Case",
            entity_id=str(existing["testcase_name"]),
            operation="delete",
            note=f"Test case '{existing['testcase_name']}' deleted (v2)",
        )

    return {"message": "Test case deleted successfully"}


