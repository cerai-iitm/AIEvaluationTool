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
from schemas import (
    TestCaseCreateV2,
    TestCaseDetailResponse,
    TestCaseListResponse,
    TestCaseUpdateV2,
)
from utils.activity_logger import log_activity

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
    return db.list_testcases_with_metadata() or []


@testcase_router.get(
    "/{testcase_id}",
    response_model=TestCaseDetailResponse,
    summary="Get a test case by ID (v2)",
)
def get_testcase(testcase_id: int, db: DB = Depends(_get_db)):
    testcase = db.get_testcase_with_metadata(testcase_id)
    if testcase is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Test case not found")
    return testcase


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
    lang_id, domain_id = _get_default_language_and_domain(db)
    prompt = Prompt(
        user_prompt=payload.user_prompt.strip(),
        system_prompt=_normalize_optional(payload.system_prompt),
        lang_id=lang_id,
        domain_id=domain_id,
    )

    response_obj = None
    normalized_response = _normalize_optional(payload.response_text)
    if normalized_response:
        response_obj = ResponseData(
            response_text=normalized_response,
            response_type="GT",
            lang_id=lang_id,
        )

    judge_prompt_obj = None
    normalized_judge_prompt = _normalize_optional(payload.llm_judge_prompt)
    if normalized_judge_prompt:
        judge_prompt_obj = LLMJudgePrompt(prompt=normalized_judge_prompt, lang_id=lang_id)

    testcase_model = TestCaseModel(
        name=payload.testcase_name.strip(),
        metric="Unknown",
        prompt=prompt,
        response=response_obj,
        strategy=payload.strategy_name.strip(),
        judge_prompt=judge_prompt_obj,
    )

    testcase_id = db.add_testcase(testcase_model)
    if testcase_id == -1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A test case with the same configuration already exists.",
        )

    created = db.get_testcase_with_metadata(testcase_id)
    if created is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Test case created but could not be loaded.",
        )

    username = _get_username_from_token(authorization)
    if username:
        log_activity(
            username=username,
            entity_type="Test Case",
            entity_id=str(created["testcase_name"]),
            operation="create",
            note=f"Test case '{created['testcase_name']}' created (v2)",
        )

    return created


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
        existing = db.get_testcase_with_metadata(testcase_id)
        if existing is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Test case not found")
        return existing

    try:
        updated = db.update_testcase_record(testcase_id, normalized_updates)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    if updated is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Test case not found")

    username = _get_username_from_token(authorization)
    if username:
        log_activity(
            username=username,
            entity_type="Test Case",
            entity_id=str(updated["testcase_name"]),
            operation="update",
            note="Test case updated via v2 endpoint",
        )

    return updated


@testcase_router.delete(
    "/delete/{testcase_id}",
    summary="Delete a test case (v2)",
)
def delete_testcase(
    testcase_id: int,
    db: DB = Depends(_get_db),
    authorization: Optional[str] = Header(None),
):
    existing = db.get_testcase_with_metadata(testcase_id)
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


