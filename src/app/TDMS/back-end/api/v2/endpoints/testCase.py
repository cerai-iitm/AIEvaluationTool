from typing import List, Optional
import json
import time
from config.settings import settings
from database.fastapi_deps import _get_db
from fastapi import APIRouter, Depends, Header, HTTPException, status
from fastapi.responses import StreamingResponse
from jose import JWTError, jwt
from schemas import (
    TestCaseCreateV2,
    TestCaseDetailResponse,
    TestCaseListResponse,
    TestCaseUpdateV2,
)
from sqlalchemy.orm import joinedload
from utils.activity_logger import log_activity

from lib.data.llm_judge_prompt import LLMJudgePrompt
from lib.data.prompt import Prompt
from lib.data.response import Response as ResponseData
from lib.data.response import Response
from lib.data.test_case import TestCase as TestCaseModel
from lib.orm.DB import DB
from lib.orm.tables import Prompts, TestCases, Metrics

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
    response_model=List[TestCaseListResponse],
    summary="List all test cases (v2)",
)
def list_testcases(db: DB = Depends(_get_db)):
    with db.Session() as session:
        testcases = (
            session.query(TestCases)
            .options(joinedload(TestCases.judge_prompt))
            .options(joinedload(TestCases.prompt))
            .options(joinedload(TestCases.response))
            .options(joinedload(TestCases.strategy))
            .options(joinedload(TestCases.metrics))
            .all()
        )
        if not testcases:
            raise HTTPException(status_code=404, detail="No test cases found")
        
        results = []
        
        for testcase in testcases:
            # Get metric names as a list
            metric_name_list = [m.metric_name for m in testcase.metrics] if testcase.metrics else []
            # Get metric names as a comma-separated string for backward compatibility
            metric_names = ", ".join(metric_name_list) if metric_name_list else ""
            
            results.append(TestCaseListResponse(
                testcase_id=testcase.testcase_id,
                testcase_name=testcase.testcase_name,
                user_prompt=testcase.prompt.user_prompt,
                system_prompt=testcase.prompt.system_prompt,
                response_text=testcase.response.response_text,
                strategy_name=getattr(testcase.strategy, "strategy_name", ""),  # Get strategy name as string
                llm_judge_prompt=getattr(testcase.judge_prompt, "prompt", None),
                domain_name=str(testcase.prompt.domain.domain_name),  # Convert to string
                lang_name=str(testcase.prompt.lang.lang_name),      # Convert to string
                metric_name=metric_names,  # Use the joined metric names for backward compatibility
                metric_name_list=metric_name_list  # List of metric names
            ))
        
        return results

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
                    if metric:
                        testcase_in_session.metrics.append(metric)
                    else:
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"Metric '{metric_name}' not found.",
                        )
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
