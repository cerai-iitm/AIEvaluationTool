from fastapi import APIRouter, HTTPException, Depends, Header
from fastapi.responses import JSONResponse
from schemas import TestCaseIds, TestCaseUpdate, TestCaseCreate, TestCaseId
from database.fastapi_deps import _get_db
from database.database import get_current_user
from models import user as user_model
from utils.activity_logger import log_activity
from jose import jwt, JWTError
from config.settings import settings
from typing import Optional
import os
import sys
import hashlib

# Ensure the project 'src' directory is on sys.path so we can import lib.orm
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../../")))
# sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../database")))

from lib.orm.DB import DB
from lib.orm.tables import TestCases, Prompts, Responses, Strategies, LLMJudgePrompts, Languages, Domains
from sqlalchemy.orm import joinedload


testcase_router = APIRouter(prefix="/api/testcases")


def get_username_from_token(authorization: Optional[str] = Header(None)) -> Optional[str]:
    """Extract username from JWT token."""
    if not authorization:
        return None
    
    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            return None
    except ValueError:
        return None
    
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload.get("user_name")
    except JWTError:
        return None

@testcase_router.get("", summary="Get all test cases", response_model=list[TestCaseIds])
async def list_testcases( db: DB = Depends(_get_db)):
    session = db.Session()
    try:
        testcases = session.query(TestCases).all()
        return [
            TestCaseIds(
                testcase_id = tc.testcase_id,
                testcase_name = tc.testcase_name,
                strategy_name = getattr(tc.strategy, "strategy_name", None) if tc.strategy else None,
                llm_judge_prompt = getattr(tc.judge_prompt, "prompt", None) if tc.judge_prompt else None,
                domain_name = getattr(getattr(tc.prompt, "domain", None), "domain_name", None) if tc.prompt and tc.prompt.domain else None,
                user_prompt = getattr(tc.prompt, "user_prompt", None) if tc.prompt else None,
                system_prompt = getattr(tc.prompt, "system_prompt", None) if tc.prompt else None,
                response_text = getattr(tc.response, "response_text", None) if tc.response else None
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

        # Defensive attribute access for all possible None objects
        strategy_name = getattr(tc.strategy, "strategy_name", None) if tc.strategy else None
        llm_judge_prompt = getattr(tc.judge_prompt, "prompt", None) if tc.judge_prompt else None
        domain_name = getattr(getattr(tc.prompt, "domain", None), "domain_name", None) if tc.prompt and tc.prompt.domain else None
        user_prompt = getattr(tc.prompt, "user_prompt", None) if tc.prompt else None
        system_prompt = getattr(tc.prompt, "system_prompt", None) if tc.prompt else None
        response_text = getattr(tc.response, "response_text", None) if tc.response else None

        return TestCaseIds(
            testcase_id = tc.testcase_id,
            testcase_name = tc.testcase_name,
            strategy_name = strategy_name,
            llm_judge_prompt = llm_judge_prompt,
            domain_name = domain_name,
            user_prompt = user_prompt,
            system_prompt = system_prompt,
            response_text = response_text
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
async def update_testcase(
    testcase_id: int, 
    testcase: TestCaseId, 
    db: DB = Depends(_get_db),
    authorization: Optional[str] = Header(None)
):
    session = db.Session()
    try:
        tc = session.query(TestCases).filter(TestCases.testcase_id == testcase_id).first()
        if not tc:
            raise HTTPException(status_code=404, detail="Test case not found")
        
        # Store original testcase name for logging
        original_name = tc.testcase_name
        
        # Update testcase_name if provided
        if testcase.testcase_name is not None:
            tc.testcase_name = testcase.testcase_name

        # Update prompt fields if provided
        if tc.prompt:
            # Check if any prompt fields have actually changed
            user_prompt_changed = testcase.user_prompt is not None and testcase.user_prompt != tc.prompt.user_prompt
            system_prompt_changed = testcase.system_prompt is not None and testcase.system_prompt != tc.prompt.system_prompt
            
            if user_prompt_changed or system_prompt_changed:
                new_user_prompt = testcase.user_prompt if testcase.user_prompt is not None else tc.prompt.user_prompt
                new_system_prompt = testcase.system_prompt if testcase.system_prompt is not None else tc.prompt.system_prompt
                
                # Compute hash the same way as in Prompt.digest
                prompt_str = f"System: '{new_system_prompt or ''}'\tUser: '{new_user_prompt}'"
                hashing = hashlib.sha1()
                hashing.update(prompt_str.encode('utf-8'))
                new_hash = hashing.hexdigest()
                
                # Check if a prompt with this hash already exists (excluding current prompt)
                existing_prompt = session.query(Prompts).filter(
                    Prompts.hash_value == new_hash,
                    Prompts.prompt_id != tc.prompt.prompt_id
                ).first()
                
                if existing_prompt:
                    # If a prompt with this hash exists, point test case to that prompt
                    tc.prompt_id = existing_prompt.prompt_id
                else:
                    # Update the current prompt's fields and hash
                    if user_prompt_changed:
                        tc.prompt.user_prompt = testcase.user_prompt
                    if system_prompt_changed:
                        tc.prompt.system_prompt = testcase.system_prompt
                    tc.prompt.hash_value = new_hash

        # Update response_text if provided
        if testcase.response_text is not None:
            if tc.response:
                # Skip if text hasn't actually changed
                if tc.response.response_text != testcase.response_text:
                    # Compute the new hash for the updated response text
                    response_str = f"Response Text: '{testcase.response_text}'\tResponse Type: '{tc.response.response_type}'"
                    hashing = hashlib.sha1()
                    hashing.update(response_str.encode('utf-8'))
                    new_hash = hashing.hexdigest()
                    
                    # Check if a response with this hash already exists (excluding current response)
                    existing_response = session.query(Responses).filter(
                        Responses.hash_value == new_hash,
                        Responses.response_id != tc.response.response_id
                    ).first()
                    
                    if existing_response:
                        # If a response with this hash exists, point test case to that response
                        tc.response_id = existing_response.response_id
                    else:
                        # Update the current response's text and hash
                        tc.response.response_text = testcase.response_text
                        tc.response.hash_value = new_hash
            else:
                # If no response exists, we might need to create one
                # For now, we'll skip if response doesn't exist
                pass

        # Update strategy_id if strategy_name is provided
        if testcase.strategy_name is not None:
            # Look up strategy by name and update the test case's strategy_id
            strategy = session.query(Strategies).filter(Strategies.strategy_name == testcase.strategy_name).first()
            if strategy:
                tc.strategy_id = strategy.strategy_id
            else:
                raise HTTPException(status_code=404, detail=f"Strategy '{testcase.strategy_name}' not found")

        # Update llm_judge_prompt if provided
        if testcase.llm_judge_prompt is not None:
            if tc.judge_prompt:
                # Skip if prompt hasn't actually changed
                if tc.judge_prompt.prompt != testcase.llm_judge_prompt:
                    # Compute hash the same way as in LLMJudgePrompt.digest (just the prompt text)
                    hashing = hashlib.sha1()
                    hashing.update(testcase.llm_judge_prompt.encode('utf-8'))
                    new_hash = hashing.hexdigest()
                    
                    # Check if a judge prompt with this hash already exists (excluding current judge_prompt)
                    existing_judge_prompt = session.query(LLMJudgePrompts).filter(
                        LLMJudgePrompts.hash_value == new_hash,
                        LLMJudgePrompts.prompt_id != tc.judge_prompt.prompt_id
                    ).first()
                    
                    if existing_judge_prompt:
                        # If a judge prompt with this hash exists, point test case to that judge prompt
                        tc.judge_prompt_id = existing_judge_prompt.prompt_id
                    else:
                        # Update the current judge prompt's text and hash
                        tc.judge_prompt.prompt = testcase.llm_judge_prompt
                        tc.judge_prompt.hash_value = new_hash
            else:
                # If no judge_prompt exists, we might need to create one
                # For now, we'll skip if judge_prompt doesn't exist
                pass

        session.commit()
        session.refresh(tc)

        # Log the activity
        username = get_username_from_token(authorization)
        if username:
            # Determine what changed for the note
            changes = []
            if testcase.testcase_name is not None and testcase.testcase_name != original_name:
                changes.append(f"name changed to '{tc.testcase_name}'")
            if testcase.user_prompt is not None or testcase.system_prompt is not None:
                changes.append("prompt updated")
            if testcase.response_text is not None:
                changes.append("response updated")
            if testcase.strategy_name is not None:
                changes.append("strategy updated")
            if testcase.llm_judge_prompt is not None:
                changes.append("judge prompt updated")
            
            note = f"Test case '{tc.testcase_name}' updated"
            if changes:
                note += f": {', '.join(changes)}"
            else:
                note += " (no changes detected)"
            
            log_activity(
                username=username,
                entity_type="Test Case",
                entity_id=str(tc.testcase_name),
                operation="update",
                note=note
            )

        # Safely retrieve related information for response model from database object
        strategy_name = getattr(tc.strategy, "strategy_name", None) if tc.strategy else None
        llm_judge_prompt = getattr(tc.judge_prompt, "prompt", None) if tc.judge_prompt else None
        domain_name = getattr(getattr(tc.prompt, "domain", None), "domain_name", None) if tc.prompt and tc.prompt.domain else None
        user_prompt = getattr(tc.prompt, "user_prompt", None) if tc.prompt else None
        system_prompt = getattr(tc.prompt, "system_prompt", None) if tc.prompt else None
        response_text = getattr(tc.response, "response_text", None) if tc.response else None

        return TestCaseUpdate(
            testcase_id=tc.testcase_id, 
            testcase_name=tc.testcase_name, 
            strategy_id=tc.strategy_id,
            strategy_name=strategy_name, 
            llm_judge_prompt_id=tc.judge_prompt_id,
            llm_judge_prompt=llm_judge_prompt, 
            domain_name=domain_name, 
            prompt_id=tc.prompt_id,
            user_prompt=user_prompt, 
            system_prompt=system_prompt, 
            response_id=tc.response_id,
            response_text=response_text
            )
    finally:
        session.close()


@testcase_router.post("/create", response_model=TestCaseIds)
async def create_testcase(
    testcase: TestCaseCreate, 
    db: DB = Depends(_get_db),
    authorization: Optional[str] = Header(None)
):
    session = db.Session()
    try:
        # 1. Check if testcase_name already exists
        existing_testcase = session.query(TestCases).filter(
            TestCases.testcase_name == testcase.testcase_name
        ).first()
        if existing_testcase:
            raise HTTPException(
                status_code=400, 
                detail=f"Test case with name '{testcase.testcase_name}' already exists"
            )

        # 2. Find Strategy by name
        strategy = session.query(Strategies).filter(
            Strategies.strategy_name == testcase.strategy_name
        ).first()
        if not strategy:
            raise HTTPException(
                status_code=404, 
                detail=f"Strategy '{testcase.strategy_name}' not found"
            )
        strategy_id = strategy.strategy_id

        # 3. Find or create Prompt
        # Compute hash for prompt
        # Handle system_prompt: can be empty string, treat as None for database
        system_prompt_value = testcase.system_prompt.strip() if testcase.system_prompt else ""
        system_prompt_db = system_prompt_value if system_prompt_value else None
        
        prompt_str = f"System: '{system_prompt_value}'\tUser: '{testcase.user_prompt}'"
        hashing = hashlib.sha1()
        hashing.update(prompt_str.encode('utf-8'))
        prompt_hash = hashing.hexdigest()

        # Check if prompt with this hash already exists
        existing_prompt = session.query(Prompts).filter(
            Prompts.hash_value == prompt_hash
        ).first()

        if existing_prompt:
            prompt_id = existing_prompt.prompt_id
        else:
            # Create new prompt - need lang_id and domain_id
            # Get default language (first one) or raise error
            default_lang = session.query(Languages).first()
            if not default_lang:
                raise HTTPException(
                    status_code=500, 
                    detail="No languages found in database. Please add a language first."
                )
            
            # Get default domain (first one) or raise error
            default_domain = session.query(Domains).first()
            if not default_domain:
                raise HTTPException(
                    status_code=500, 
                    detail="No domains found in database. Please add a domain first."
                )

            new_prompt = Prompts(
                user_prompt=testcase.user_prompt,
                system_prompt=system_prompt_db,
                lang_id=default_lang.lang_id,
                domain_id=default_domain.domain_id,
                hash_value=prompt_hash
            )
            session.add(new_prompt)
            session.flush()  # Flush to get the prompt_id
            prompt_id = new_prompt.prompt_id

        # 4. Find or create Response
        response_id = None
        if testcase.response_text and testcase.response_text.strip():
            # Compute hash for response
            response_str = f"Response Text: '{testcase.response_text}'\tResponse Type: 'GT'"
            hashing = hashlib.sha1()
            hashing.update(response_str.encode('utf-8'))
            response_hash = hashing.hexdigest()

            # Check if response with this hash already exists
            existing_response = session.query(Responses).filter(
                Responses.hash_value == response_hash
            ).first()

            if existing_response:
                response_id = existing_response.response_id
            else:
                # Create new response
                # Get default language
                default_lang = session.query(Languages).first()
                if not default_lang:
                    raise HTTPException(
                        status_code=500, 
                        detail="No languages found in database. Please add a language first."
                    )

                new_response = Responses(
                    response_text=testcase.response_text,
                    response_type='GT',  # Default to Ground Truth
                    prompt_id=prompt_id,
                    lang_id=default_lang.lang_id,
                    hash_value=response_hash
                )
                session.add(new_response)
                session.flush()  # Flush to get the response_id
                response_id = new_response.response_id

        # 5. Find or create LLMJudgePrompt (if provided)
        judge_prompt_id = None
        if testcase.llm_judge_prompt:
            # Compute hash for LLM judge prompt
            hashing = hashlib.sha1()
            hashing.update(testcase.llm_judge_prompt.encode('utf-8'))
            judge_prompt_hash = hashing.hexdigest()

            # Check if judge prompt with this hash already exists
            existing_judge_prompt = session.query(LLMJudgePrompts).filter(
                LLMJudgePrompts.hash_value == judge_prompt_hash
            ).first()

            if existing_judge_prompt:
                judge_prompt_id = existing_judge_prompt.prompt_id
            else:
                # Create new judge prompt
                # Get default language
                default_lang = session.query(Languages).first()
                if not default_lang:
                    raise HTTPException(
                        status_code=500, 
                        detail="No languages found in database. Please add a language first."
                    )

                new_judge_prompt = LLMJudgePrompts(
                    prompt=testcase.llm_judge_prompt,
                    lang_id=default_lang.lang_id,
                    hash_value=judge_prompt_hash
                )
                session.add(new_judge_prompt)
                session.flush()  # Flush to get the prompt_id
                judge_prompt_id = new_judge_prompt.prompt_id

        # 6. Create TestCase
        tc = TestCases(
            testcase_name=testcase.testcase_name,
            strategy_id=strategy_id,
            prompt_id=prompt_id,
            response_id=response_id,
            judge_prompt_id=judge_prompt_id
        )

        session.add(tc)
        session.commit()
        session.refresh(tc)
        
        # Log the activity
        username = get_username_from_token(authorization)
        if username:
            log_activity(
                username=username,
                entity_type="Test Case",
                entity_id=str(tc.testcase_name),
                operation="create",
                note=f"Test case '{tc.testcase_name}' created"
            )
        
        # Safely retrieve related information for response
        strategy_name = getattr(tc.strategy, "strategy_name", None) if tc.strategy else None
        llm_judge_prompt = getattr(tc.judge_prompt, "prompt", None) if tc.judge_prompt else None
        domain_name = getattr(getattr(tc.prompt, "domain", None), "domain_name", None) if tc.prompt and tc.prompt.domain else None
        user_prompt = getattr(tc.prompt, "user_prompt", None) if tc.prompt else None
        system_prompt = getattr(tc.prompt, "system_prompt", None) if tc.prompt else None
        response_text = getattr(tc.response, "response_text", None) if tc.response else None

        return TestCaseIds(
            testcase_id=tc.testcase_id, 
            testcase_name=tc.testcase_name, 
            strategy_name=strategy_name, 
            llm_judge_prompt=llm_judge_prompt, 
            domain_name=domain_name, 
            user_prompt=user_prompt, 
            system_prompt=system_prompt, 
            response_text=response_text
        )
    except HTTPException:
        session.rollback()
        raise
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Error creating test case: {str(e)}")
    finally:
        session.close()


@testcase_router.delete("/{testcase_id}")
async def delete_testcase(
    testcase_id: int, 
    db: DB = Depends(_get_db),
    authorization: Optional[str] = Header(None)
):
    session = db.Session()
    try:
        tc = session.query(TestCases).filter(TestCases.testcase_id == testcase_id).first()
        if not tc:
            raise HTTPException(status_code=404, detail="Test case not found")
        
        # Store testcase name for logging before deletion
        testcase_name = tc.testcase_name
        testcase_id_str = str(tc.testcase_id)
        
        session.delete(tc)
        session.commit()
        
        # Log the activity
        username = get_username_from_token(authorization)
        if username:
            log_activity(
                username=username,
                entity_type="Test Case",
                entity_id=testcase_name,
                operation="delete",
                note=f"Test case '{testcase_name}' deleted"
            )
        
        return JSONResponse(content={"message": "Test case deleted successfully"}, status_code=200)
    finally:
        session.close()
