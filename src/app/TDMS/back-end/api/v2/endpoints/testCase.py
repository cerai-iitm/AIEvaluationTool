from typing import Any, Dict, List, Optional
import errno
import json
import time
from pathlib import Path
from config.settings import settings
from database.fastapi_deps import _get_db
from fastapi import APIRouter, Depends, File, Header, HTTPException, UploadFile, status
from fastapi.responses import StreamingResponse
from jose import JWTError, jwt
from pydantic import ValidationError
from schemas import (
    TestCaseCreateV2,
    TestCaseDetailResponse,
    TestCaseListResponse,
    TestCasePageResponse,
    TestCaseUpdateV2,
)
from sqlalchemy import func
from sqlalchemy.orm import joinedload
from utils.activity_logger import log_activity

from lib.data.llm_judge_prompt import LLMJudgePrompt
from lib.data.prompt import Prompt
from lib.data.response import Response as ResponseData
from lib.data.response import Response
from lib.data.test_case import TestCase as TestCaseModel
from lib.orm.DB import DB
from lib.orm.tables import Domains, Languages, MetricTestCaseMapping, Prompts, Strategies, TestCases, Metrics

testcase_router = APIRouter(prefix="/api/v2/testcases")


def _normalize_optional(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    return value


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

@testcase_router.get(
    "",
    response_model=TestCasePageResponse,
    summary="List all test cases (v2)",
)
def list_testcases(
    limit: int = 15,
    offset: int = 0,
    search: Optional[str] = None,
    field: Optional[str] = None,
    db: DB = Depends(_get_db),
):
    limit = max(1, min(limit, 100))
    offset = max(0, offset)

    with db.Session() as session:
        base_query = (
            session.query(TestCases)
            .join(Prompts, TestCases.prompt_id == Prompts.prompt_id)
            .join(Strategies, TestCases.strategy_id == Strategies.strategy_id)
            .join(Domains, Prompts.domain_id == Domains.domain_id)
            .join(Languages, Prompts.lang_id == Languages.lang_id)
        )

        search_value = search.strip() if search else ""
        if search_value:
            search_filter = f"%{search_value.lower()}%"
            if field == "strategy":
                base_query = base_query.filter(func.lower(Strategies.strategy_name).like(search_filter))
            elif field == "domain":
                base_query = base_query.filter(func.lower(Domains.domain_name).like(search_filter))
            elif field == "metric":
                base_query = (
                    base_query
                    .outerjoin(MetricTestCaseMapping, TestCases.testcase_id == MetricTestCaseMapping.testcase_id)
                    .outerjoin(Metrics, MetricTestCaseMapping.metric_id == Metrics.metric_id)
                    .filter(func.lower(Metrics.metric_name).like(search_filter))
                )
            else:
                base_query = base_query.filter(func.lower(TestCases.testcase_name).like(search_filter))

        total = (
            base_query
            .with_entities(func.count(func.distinct(TestCases.testcase_id)))
            .scalar()
            or 0
        )

        testcase_ids = [
            row[0]
            for row in (
                base_query
                .with_entities(TestCases.testcase_id)
                .distinct()
                .order_by(TestCases.testcase_id)
                .offset(offset)
                .limit(limit)
                .all()
            )
        ]

        if not testcase_ids:
            return TestCasePageResponse(items=[], total=total, limit=limit, offset=offset)

        rows = (
            session.query(
                TestCases.testcase_id,
                TestCases.testcase_name,
                Strategies.strategy_name,
                Domains.domain_name,
                Languages.lang_name,
                Metrics.metric_name,
            )
            .join(Prompts, TestCases.prompt_id == Prompts.prompt_id)
            .join(Strategies, TestCases.strategy_id == Strategies.strategy_id)
            .join(Domains, Prompts.domain_id == Domains.domain_id)
            .join(Languages, Prompts.lang_id == Languages.lang_id)
            .outerjoin(MetricTestCaseMapping, TestCases.testcase_id == MetricTestCaseMapping.testcase_id)
            .outerjoin(Metrics, MetricTestCaseMapping.metric_id == Metrics.metric_id)
            .filter(TestCases.testcase_id.in_(testcase_ids))
            .order_by(TestCases.testcase_id)
            .all()
        )

        results_by_id: Dict[int, TestCaseListResponse] = {}
        for row in rows:
            existing = results_by_id.get(row.testcase_id)
            if existing is None:
                existing = TestCaseListResponse(
                    testcase_id=row.testcase_id,
                    testcase_name=row.testcase_name,
                    strategy_name=row.strategy_name,
                    domain_name=row.domain_name,
                    lang_name=row.lang_name,
                    metric_name="",
                    metric_name_list=[],
                )
                results_by_id[row.testcase_id] = existing

            if row.metric_name and row.metric_name not in existing.metric_name_list:
                existing.metric_name_list.append(row.metric_name)

        results = []
        for testcase_id in testcase_ids:
            result = results_by_id[testcase_id]
            result.metric_name = ", ".join(result.metric_name_list)
            results.append(result)
        
        return TestCasePageResponse(items=results, total=total, limit=limit, offset=offset)

    # testcases = db.testcases

    # results = []
    # for testcase in testcases:
    #     domain_name = db.get_domain_name(testcase.prompt.domain_id)
    #     lang_name = db.get_language_name(testcase.prompt.lang_id)
    #     response_str = (
    #         testcase.response.response_text
    #         if hasattr(testcase.response, "response_text")
    #         else str(testcase.response)
    #     )
    #     judge_prompt_str = (
    #         testcase.judge_prompt.prompt
    #         if hasattr(testcase.judge_prompt, "prompt")
    #         else str(testcase.judge_prompt)
    #     )
    #     results.append(
    #         TestCaseListResponse(
    #             testcase_id=testcase.testcase_id,
    #             testcase_name=testcase.name,
    #             user_prompt=testcase.prompt.user_prompt,
    #             system_prompt=testcase.prompt.system_prompt,
    #             response_text=response_str,
    #             strategy_name=testcase.strategy,
    #             llm_judge_prompt=judge_prompt_str,
    #             domain_name=domain_name,
    #             lang_name=lang_name,
    #             metric_name=testcase.metric
    #         )
    #     )
    # return results


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
    with db.Session() as session:
        testcase = (
            session.query(TestCases)
            .options(
                joinedload(TestCases.prompt),
                joinedload(TestCases.response),
                joinedload(TestCases.strategy),
                joinedload(TestCases.judge_prompt),
                joinedload(TestCases.metrics),
            )
            .filter(TestCases.testcase_id == testcase_id)
            .first()
        )
        
        if testcase is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Test case not found"
            )

        judge_prompt = testcase.judge_prompt
        llm_judge_prompt = judge_prompt.prompt if judge_prompt else None
        
        # Get metric names as a list
        metric_name_list = [m.metric_name for m in testcase.metrics] if testcase.metrics else []
        metric_names = ", ".join(metric_name_list) if metric_name_list else ""

        return TestCaseListResponse(
            testcase_id=testcase.testcase_id,
            testcase_name=testcase.testcase_name,
            user_prompt=testcase.prompt.user_prompt if testcase.prompt else None,
            system_prompt=testcase.prompt.system_prompt if testcase.prompt else None,
            response_text=testcase.response.response_text if testcase.response else None,
            strategy_name=testcase.strategy.strategy_name if testcase.strategy else None,
            llm_judge_prompt=llm_judge_prompt,
            domain_name=testcase.prompt.domain.domain_name if testcase.prompt and testcase.prompt.domain else None,
            lang_name=testcase.prompt.lang.lang_name if testcase.prompt and testcase.prompt.lang else None,
            metric_name=metric_names,  # Comma-separated for backward compatibility
            metric_name_list=metric_name_list,  # List of metric names
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
    #try:
    # Get next available ID
    with db.Session() as session:
        #try:
        existing_ids = [
            row[0]
            for row in session.query(TestCases.testcase_id)
            .order_by(TestCases.testcase_id)
            .all()
        ]
        next_id = 1
        for id in existing_ids:
            if id != next_id:
                break
            next_id += 1

        # Convert payload to TestCase model
        prompt_lang_id = db.add_or_get_language_id(payload.language_name)
        if prompt_lang_id is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to add or get language '{payload.language_name}'.",
            )
        
        domain_id = db.add_or_get_domain_id(payload.domain_name)
        if domain_id is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to add or get domain '{payload.domain_name}'.",
            )
        
        prompt = Prompt(
            user_prompt=payload.user_prompt,
            system_prompt=payload.system_prompt if payload.system_prompt else None,
            lang_id=prompt_lang_id,
            domain_id=domain_id,
        )

        response = None
        if payload.response_text:
            # Use response_lang if provided, otherwise use the prompt's language
            response_lang_id = prompt_lang_id
            if payload.response_lang:
                response_lang_id = db.add_or_get_language_id(payload.response_lang)
                if response_lang_id is None:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Failed to add or get response language '{payload.response_lang}'.",
                    )
            
            response = ResponseData(
                response_text=payload.response_text,
                response_type=payload.response_type or "GT",  # Default to Ground Truth
                lang_id=response_lang_id,
            )

        judge_prompt = None
        if payload.llm_judge_prompt:
            judge_prompt = LLMJudgePrompt(
                prompt=payload.llm_judge_prompt,
                lang_id=prompt_lang_id,  # Use the prompt's language ID
            )

        # Handle metric_name_list - use first metric for backward compatibility with TestCaseModel
        metric_name_for_model = payload.metric_name
        if payload.metric_name_list and len(payload.metric_name_list) > 0:
            metric_name_for_model = payload.metric_name_list[0]
        elif not metric_name_for_model:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least one metric name is required (metric_name_list).",
            )

        testcase = TestCaseModel(
            name=payload.testcase_name,
            prompt=prompt,
            response=response,
            judge_prompt=judge_prompt,
            strategy=payload.strategy_name,
            metric=metric_name_for_model,
        )

        # Add test case with custom ID
        testcase_obj = db._DB__add_or_get_test_case_custom_id(testcase, next_id)
        if not testcase_obj:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to create test case. It may already exist.",
            )
        
        # Handle multiple metrics if metric_name_list is provided
        if payload.metric_name_list and len(payload.metric_name_list) > 0:
            with db.Session() as session:
                # Re-query the testcase within this session to avoid detached instance error
                testcase_in_session = (
                    session.query(TestCases)
                    .options(joinedload(TestCases.metrics))
                    .filter(TestCases.testcase_id == testcase_obj.testcase_id)
                    .first()
                )
                
                if not testcase_in_session:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="Test case not found after creation",
                    )
                
                # Clear existing metrics
                testcase_in_session.metrics.clear()
                # Add all metrics from the list
                for metric_name in payload.metric_name_list:
                    metric = session.query(Metrics).filter(Metrics.metric_name == metric_name).first()
                    if not metric:
                        metric = Metrics(metric_name=metric_name, domain_id=domain_id)
                        session.add(metric)
                        session.flush()
                    testcase_in_session.metrics.append(metric)
                session.commit()
                session.refresh(testcase_in_session)

        # Get the created test case with all relationships loaded
        # This is necessary because the object returned from __add_or_get_test_case_custom_id
        # is detached from the session, so we need to re-query with eager loading
        with db.Session() as session:
            testcase_full = (
                session.query(TestCases)
                .options(
                    joinedload(TestCases.prompt),
                    joinedload(TestCases.response),
                    joinedload(TestCases.strategy),
                    joinedload(TestCases.judge_prompt),
                    joinedload(TestCases.metrics),
                )
                .filter(TestCases.testcase_id == testcase_obj.testcase_id)
                .first()
            )

            if not testcase_full:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Test case not found after creation",
                )

            # Log activity
            username = _get_username_from_token(authorization)
            if username:
                log_activity(
                    username=username,
                    entity_type="Test Case",
                    entity_id=str(testcase_full.testcase_id),
                    operation="create",
                    note=f"Test Case - {testcase_full.testcase_name} created",
                    user_note=payload.notes,
                )

            # Get domain and language names
            domain_name = None
            lang_name = None
            if testcase_full.prompt:
                if testcase_full.prompt.domain:
                    domain_name = testcase_full.prompt.domain.domain_name
                if testcase_full.prompt.lang_id:
                    lang_name = db.get_language_name(testcase_full.prompt.lang_id)

            # Get metric names as a list
            metric_name_list = [m.metric_name for m in testcase_full.metrics] if testcase_full.metrics else []
            metric_names = ", ".join(metric_name_list) if metric_name_list else ""

            return TestCaseDetailResponse(
                testcase_id=testcase_full.testcase_id,
                testcase_name=testcase_full.testcase_name,
                user_prompt=testcase_full.prompt.user_prompt
                if testcase_full.prompt
                else None,
                system_prompt=testcase_full.prompt.system_prompt
                if testcase_full.prompt
                else None,
                response_text=testcase_full.response.response_text
                if testcase_full.response
                else None,
                strategy_name=testcase_full.strategy.strategy_name
                if testcase_full.strategy
                else None,
                llm_judge_prompt=testcase_full.judge_prompt.prompt
                if testcase_full.judge_prompt
                else None,
                domain_name=domain_name,
                lang_name=lang_name,
                metric_name=metric_names,  # Comma-separated for backward compatibility
                metric_name_list=metric_name_list,  # List of metric names
                strategy_id=testcase_full.strategy_id,
                prompt_id=testcase_full.prompt_id,
                response_id=testcase_full.response_id,
                llm_judge_prompt_id=testcase_full.judge_prompt_id,
                domain_id=testcase_full.prompt.domain_id if testcase_full.prompt else None,
            )

        # except HTTPException:
        #     raise 
        # except Exception as e:
        #     raise HTTPException(
        #         status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        #         detail=f"An error occurred while creating the test case: {str(e)}",
        #     )


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
#         user_prompt=payload.user_prompt,
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
#         name=payload.testcase_name,
#         metric="Unknown",
#         prompt=prompt,
#         response=response_obj,
#         strategy=payload.strategy_name,
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
        normalized_updates[key] = value

    # Handle metric_name_list - convert to metric_name_list format if metric_name is provided
    if "metric_name" in normalized_updates and "metric_name_list" not in normalized_updates:
        # If only metric_name is provided, convert to list
        if normalized_updates["metric_name"]:
            normalized_updates["metric_name_list"] = [normalized_updates["metric_name"]]
        del normalized_updates["metric_name"]

    # Normalize optional fields
    for optional_field in ("response_text", "llm_judge_prompt"):
        if optional_field in normalized_updates:
            normalized_updates[optional_field] = _normalize_optional(normalized_updates[optional_field])

    if not normalized_updates:
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

    username = _get_username_from_token(authorization)
    if username:
        changes = []
        if "testcase_name" in normalized_updates:
            changes.append(f"Name changed to '{updated.testcase_name}'")
        if "user_prompt" in normalized_updates or "system_prompt" in normalized_updates:
            changes.append("prompt updated")
        if "response_text" in normalized_updates:
            changes.append("response updated")
        if "strategy_name" in normalized_updates:
            changes.append("strategy updated")
        if "metric_name" in normalized_updates or "metric_name_list" in normalized_updates:
            changes.append("metric updated")
        if "llm_judge_prompt" in normalized_updates and payload.llm_judge_prompt is not None:
            changes.append("judge prompt updated")

        note = f"Test Case - {updated.testcase_name} updated"
        if changes:
            note += f" : {', '.join(changes)}"
        else:
            note += " (no changes detected)"

        log_activity(
            username=username,
            entity_type="Test Case",
            entity_id=str(updated.testcase_id),
            operation="update",
            note=note,
            user_note=payload.notes,
        )

    # Get metric names as a list
    metric_name_list = [m.metric_name for m in updated.metrics] if updated.metrics else []
    metric_name = ", ".join(metric_name_list) if metric_name_list else ""
    
    return {
        "testcase_id": updated.testcase_id,
        "testcase_name": updated.testcase_name,
        "strategy_id": updated.strategy_id,
        "strategy_name": updated.strategy.strategy_name if updated.strategy else None,
        "llm_judge_prompt_id": updated.judge_prompt_id,
        "llm_judge_prompt": updated.judge_prompt.prompt if updated.judge_prompt else None,
        "domain_id": updated.prompt.domain_id if updated.prompt else None,
        "domain_name": updated.prompt.domain.domain_name if updated.prompt and updated.prompt.domain else None,
        "prompt_id": updated.prompt_id,
        "user_prompt": updated.prompt.user_prompt if updated.prompt else None,
        "system_prompt": updated.prompt.system_prompt if updated.prompt else None,
        "response_id": updated.response_id,
        "response_text": updated.response.response_text if updated.response else None,
        "metric_name": metric_name,  # Comma-separated for backward compatibility
        "metric_name_list": metric_name_list,  # List of metric names
    }


def _format_validation_location(location: tuple[Any, ...]) -> str:
    return ".".join(str(part) for part in location)


def _extract_testcases_from_json(payload: Any) -> list[Any]:
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict) and isinstance(payload.get("test_cases"), list):
        return payload["test_cases"]
    raise HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail={
            "message": "JSON must be an array of test cases or an object with a test_cases array.",
            "errors": [],
        },
    )


def _read_uploaded_json_file(file: UploadFile, upload_label: str) -> Any:
    if not file.filename or not file.filename.lower().endswith(".json"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please upload a .json file.",
        )

    try:
        return json.loads(file.file.read().decode("utf-8"))
    except UnicodeDecodeError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{upload_label} JSON file must be UTF-8 encoded.",
        ) from exc
    except json.JSONDecodeError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid JSON: {exc.msg} at line {exc.lineno}, column {exc.colno}.",
        ) from exc

# if the uploading sample testcases datasets no in data/ directory this router will store it in data/ directory
# @testcase_router.post(
#     "/upload-dashboard-testcases-json",
#     summary="Bulk upload dashboard dataset test cases from JSON (v2)",
# )


@testcase_router.post(
    "/upload-json",
    summary="Bulk upload test cases from JSON (v2)",
)
async def upload_testcases_json(
    file: UploadFile = File(...),
    db: DB = Depends(_get_db),
    authorization: Optional[str] = Header(None),
):
    raw_payload = _read_uploaded_json_file(file, "Test cases")
    rows = _extract_testcases_from_json(raw_payload)
    if not rows:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "message": "JSON file does not contain any test cases.",
                "errors": [],
            },
        )

    validated_rows: list[TestCaseCreateV2] = []
    errors: list[dict[str, Any]] = []
    seen_names: set[str] = set()
    required_text_fields = (
        "testcase_name",
        "user_prompt",
        "language_name",
        "domain_name",
        "strategy_name",
    )

    for index, row in enumerate(rows, start=1):
        if not isinstance(row, dict):
            errors.append({"row": index, "field": "", "message": "Each test case must be a JSON object."})
            continue

        try:
            testcase_payload = TestCaseCreateV2.model_validate(row)
        except ValidationError as exc:
            for error in exc.errors():
                errors.append(
                    {
                        "row": index,
                        "field": _format_validation_location(error["loc"]),
                        "message": error["msg"],
                    }
                )
            continue

        for field_name in required_text_fields:
            value = getattr(testcase_payload, field_name)
            if isinstance(value, str):
                value = value.strip()
                setattr(testcase_payload, field_name, value)
            if not value:
                errors.append({"row": index, "field": field_name, "message": "Field is required."})

        testcase_payload.metric_name_list = [
            metric_name.strip()
            for metric_name in testcase_payload.metric_name_list
            if metric_name and metric_name.strip()
        ]
        if not testcase_payload.metric_name_list:
            errors.append({"row": index, "field": "metric_name_list", "message": "At least one metric is required."})

        normalized_name = testcase_payload.testcase_name.strip().lower()
        if normalized_name in seen_names:
            errors.append(
                {
                    "row": index,
                    "field": "testcase_name",
                    "message": f"Duplicate testcase_name '{testcase_payload.testcase_name}' in uploaded JSON.",
                }
            )
        seen_names.add(normalized_name)
        validated_rows.append(testcase_payload)

    if errors:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "message": "JSON upload validation failed.",
                "errors": errors,
            },
        )

    with db.Session() as session:
        existing_testcase_names = {
            name
            for (name,) in session.query(TestCases.testcase_name)
            .filter(TestCases.testcase_name.in_([row.testcase_name for row in validated_rows]))
            .all()
        }

    created: list[dict[str, Any]] = []
    skipped: list[str] = []
    for testcase_payload in validated_rows:
        if testcase_payload.testcase_name in existing_testcase_names:
            skipped.append(testcase_payload.testcase_name)
            continue

        created_response = create_testcase(
            payload=testcase_payload,
            db=db,
            authorization=authorization,
        )
        created.append(created_response.model_dump())

    return {
        "message": f"Imported {len(created)} test case(s). Skipped {len(skipped)} duplicate(s).",
        "created_count": len(created),
        "skipped_count": len(skipped),
        "skipped_duplicates": skipped,
        "created": created,
    }


def _required_dashboard_value(row: dict[str, Any], key: str, row_label: str) -> str:
    value = row.get(key)
    if not isinstance(value, str) or not value.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "message": "Dashboard JSON upload validation failed.",
                "errors": [
                    {
                        "row": row_label,
                        "field": key,
                        "message": "Field is required.",
                    }
                ],
            },
        )
    return value.strip()


def _resolve_dashboard_strategy_name(db: DB, strategy_value: Any, row_label: str) -> str:
    strategy_ids = strategy_value if isinstance(strategy_value, list) else [strategy_value]
    for strategy_id in strategy_ids:
        try:
            strategy_name = db.get_strategy_name(int(strategy_id))
        except (TypeError, ValueError):
            strategy_name = None

        if strategy_name:
            return strategy_name

    raise HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail={
            "message": "Dashboard JSON upload validation failed.",
            "errors": [
                {
                    "row": row_label,
                    "field": "STRATEGY",
                    "message": f"Strategy id(s) {strategy_ids} were not found.",
                }
            ],
        },
    )


def _dashboard_dataset_to_testcase_payloads(payload: Any, db: DB) -> list[TestCaseCreateV2]:
    if not isinstance(payload, dict):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "message": "Dashboard JSON must be an object keyed by metric id.",
                "errors": [],
            },
        )

    testcases: list[TestCaseCreateV2] = []
    seen_names: set[str] = set()

    for metric_id, metric_group in payload.items():
        metric_name = None
        try:
            metric_name = db.get_metric_name(int(metric_id))
        except (TypeError, ValueError):
            pass

        if not metric_name:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "message": "Dashboard JSON upload validation failed.",
                    "errors": [
                        {
                            "row": str(metric_id),
                            "field": "metric_id",
                            "message": f"Metric id '{metric_id}' was not found.",
                        }
                    ],
                },
            )

        if not isinstance(metric_group, dict) or not isinstance(metric_group.get("cases"), list):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "message": "Dashboard JSON upload validation failed.",
                    "errors": [
                        {
                            "row": str(metric_id),
                            "field": "cases",
                            "message": "Each metric id must contain a cases array.",
                        }
                    ],
                },
            )

        for case_index, row in enumerate(metric_group["cases"], start=1):
            row_label = f"metric {metric_id}, case {case_index}"
            if not isinstance(row, dict):
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail={
                        "message": "Dashboard JSON upload validation failed.",
                        "errors": [
                            {
                                "row": row_label,
                                "field": "",
                                "message": "Each case must be a JSON object.",
                            }
                        ],
                    },
                )

            testcase_name = _required_dashboard_value(row, "PROMPT_ID", row_label)
            normalized_name = testcase_name.lower()
            if normalized_name in seen_names:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail={
                        "message": "Dashboard JSON upload validation failed.",
                        "errors": [
                            {
                                "row": row_label,
                                "field": "PROMPT_ID",
                                "message": f"Duplicate PROMPT_ID '{testcase_name}' in uploaded JSON.",
                            }
                        ],
                    },
                )
            seen_names.add(normalized_name)

            strategy_name = _resolve_dashboard_strategy_name(db, row.get("STRATEGY"), row_label)
            llm_judge_prompt = row.get("LLM_AS_JUDGE")
            if isinstance(llm_judge_prompt, str) and llm_judge_prompt.strip().lower() == "no":
                llm_judge_prompt = None

            testcases.append(
                TestCaseCreateV2(
                    testcase_name=testcase_name,
                    user_prompt=_required_dashboard_value(row, "PROMPT", row_label),
                    system_prompt=row.get("SYSTEM_PROMPT") if isinstance(row.get("SYSTEM_PROMPT"), str) else None,
                    language_name=_required_dashboard_value(row, "LANGUAGE", row_label),
                    domain_name=_required_dashboard_value(row, "DOMAIN", row_label),
                    response_text=row.get("EXPECTED_OUTPUT") if isinstance(row.get("EXPECTED_OUTPUT"), str) else None,
                    response_type="GT",
                    strategy_name=strategy_name,
                    llm_judge_prompt=llm_judge_prompt if isinstance(llm_judge_prompt, str) else None,
                    metric_name_list=[metric_name],
                )
            )

    return testcases


@testcase_router.post(
    "/upload-dashboard-json",
    summary="Bulk upload dashboard dataset test cases from JSON (v2)",
)
async def upload_dashboard_testcases_json(
    file: UploadFile = File(...),
    db: DB = Depends(_get_db),
    authorization: Optional[str] = Header(None),
):
    raw_payload = _read_uploaded_json_file(file, "Dashboard dataset")
    testcase_payloads = _dashboard_dataset_to_testcase_payloads(raw_payload, db)
    if not testcase_payloads:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "message": "Dashboard JSON file does not contain any test cases.",
                "errors": [],
            },
        )

    with db.Session() as session:
        existing_testcase_names = {
            name
            for (name,) in session.query(TestCases.testcase_name)
            .filter(TestCases.testcase_name.in_([row.testcase_name for row in testcase_payloads]))
            .all()
        }

    created: list[dict[str, Any]] = []
    skipped: list[str] = []
    for testcase_payload in testcase_payloads:
        if testcase_payload.testcase_name in existing_testcase_names:
            skipped.append(testcase_payload.testcase_name)
            continue

        created_response = create_testcase(
            payload=testcase_payload,
            db=db,
            authorization=authorization,
        )
        created.append(created_response.model_dump())

    return {
        "message": f"Imported {len(created)} dashboard test case(s). Skipped {len(skipped)} duplicate(s).",
        "created_count": len(created),
        "skipped_count": len(skipped),
        "skipped_duplicates": skipped,
        "created": created,
    }


# @testcase_router.post(
#     "/upload-json",
#     summary="Bulk upload test cases from JSON (v2)",
# )
# async def upload_testcases_json(
#     file: UploadFile = File(...),
#     db: DB = Depends(_get_db),
#     authorization: Optional[str] = Header(None),
# ):
#     if not file.filename or not file.filename.lower().endswith(".json"):
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail="Please upload a .json file.",
#         )

#     try:
#         raw_payload = json.loads((await file.read()).decode("utf-8"))
#     except UnicodeDecodeError as exc:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail="JSON file must be UTF-8 encoded.",
#         ) from exc
#     except json.JSONDecodeError as exc:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail=f"Invalid JSON: {exc.msg} at line {exc.lineno}, column {exc.colno}.",
#         ) from exc

#     rows = _extract_testcases_from_json(raw_payload)
#     if not rows:
#         raise HTTPException(
#             status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
#             detail={
#                 "message": "JSON file does not contain any test cases.",
#                 "errors": [],
#             },
#         )

#     validated_rows: list[TestCaseCreateV2] = []
#     errors: list[dict[str, Any]] = []
#     seen_names: set[str] = set()
#     required_text_fields = (
#         "testcase_name",
#         "user_prompt",
#         "language_name",
#         "domain_name",
#         "strategy_name",
#     )

#     for index, row in enumerate(rows, start=1):
#         if not isinstance(row, dict):
#             errors.append(
#                 {
#                     "row": index,
#                     "field": "",
#                     "message": "Each test case must be a JSON object.",
#                 }
#             )
#             continue

#         try:
#             testcase_payload = TestCaseCreateV2.model_validate(row)
#         except ValidationError as exc:
#             for error in exc.errors():
#                 errors.append(
#                     {
#                         "row": index,
#                         "field": _format_validation_location(error["loc"]),
#                         "message": error["msg"],
#                     }
#                 )
#             continue

#         for field_name in required_text_fields:
#             value = getattr(testcase_payload, field_name)
#             if isinstance(value, str):
#                 setattr(testcase_payload, field_name, value.strip())
#             if not value or not value.strip():
#                 errors.append(
#                     {
#                         "row": index,
#                         "field": field_name,
#                         "message": "Field is required.",
#                     }
#                 )

#         testcase_payload.metric_name_list = [
#             metric_name.strip() for metric_name in testcase_payload.metric_name_list
#         ]
#         if not testcase_payload.metric_name_list:
#             errors.append(
#                 {
#                     "row": index,
#                     "field": "metric_name_list",
#                     "message": "At least one metric is required.",
#                 }
#             )
#         else:
#             seen_metrics: set[str] = set()
#             for metric_name in testcase_payload.metric_name_list:
#                 normalized_metric = metric_name.strip().lower()
#                 if not normalized_metric:
#                     errors.append(
#                         {
#                             "row": index,
#                             "field": "metric_name_list",
#                             "message": "Metric names cannot be blank.",
#                         }
#                     )
#                     continue
#                 if normalized_metric in seen_metrics:
#                     errors.append(
#                         {
#                             "row": index,
#                             "field": "metric_name_list",
#                             "message": f"Duplicate metric '{metric_name}' in the same test case.",
#                         }
#                     )
#                 seen_metrics.add(normalized_metric)

#         normalized_name = testcase_payload.testcase_name.strip().lower()
#         if normalized_name in seen_names:
#             errors.append(
#                 {
#                     "row": index,
#                     "field": "testcase_name",
#                     "message": f"Duplicate testcase_name '{testcase_payload.testcase_name}' in uploaded JSON.",
#                 }
#             )
#         seen_names.add(normalized_name)
#         validated_rows.append(testcase_payload)

#     metric_names = sorted({metric for row in validated_rows for metric in row.metric_name_list})
#     with db.Session() as session:
#         existing_testcase_names = {
#             name
#             for (name,) in session.query(TestCases.testcase_name)
#             .filter(TestCases.testcase_name.in_([row.testcase_name for row in validated_rows]))
#             .all()
#         }

#     if errors:
#         raise HTTPException(
#             status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
#             detail={
#                 "message": "JSON upload validation failed.",
#                 "errors": errors,
#             },
#         )

#     created: list[dict[str, Any]] = []
#     skipped: list[str] = []

#     for testcase_payload in validated_rows:
#         if testcase_payload.testcase_name in existing_testcase_names:
#             skipped.append(testcase_payload.testcase_name)
#             continue

#         created_response = create_testcase(
#             payload=testcase_payload,
#             db=db,
#             authorization=authorization,
#         )
#         created.append(created_response.model_dump())

#     return {
#         "message": f"Imported {len(created)} test case(s). Skipped {len(skipped)} duplicate(s).",
#         "created_count": len(created),
#         "skipped_count": len(skipped),
#         "skipped_duplicates": skipped,
#         "created": created,
#     }



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
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Test case not found"
        )

    if not db.delete_testcase_record(testcase_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Test case not found"
        )

    username = _get_username_from_token(authorization)
    if username:
        log_activity(
            username=username,
            entity_type="Test Case",
            entity_id=str(testcase_id),
            operation="delete",
            note=f"Test case - {existing.name} deleted",
            user_note=None,  # Delete operations don't have user notes from payload
        )

    return {"message": "Test case deleted successfully"}
