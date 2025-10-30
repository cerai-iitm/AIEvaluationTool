from sqlalchemy.orm import Session
from schemas import TestCase
from config import helpers
from fastapi import HTTPException   


def create_testcase(db: Session, testcase: TestCase):
    try:
        new_testcase = TestCases(**testcase.dict())
        db.add(new_testcase)
        db.commit()
        db.refresh(new_testcase)
        return new_testcase
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


def get_testcase(db: Session, testcase_id: int):
    try:
        return db.query(TestCases).filter(TestCases.testcase_id == testcase_id).first()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


def get_testcase_by_name(db: Session, testcase_name: str):
    try:
        return db.query(TestCases).filter(TestCases.name == testcase_name).first()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


def update_testcase(db: Session, testcase_id: int, testcase: TestCase):
    try:
        db.query(TestCases).filter(TestCases.testcase_id == testcase_id).update(testcase.dict())
        db.commit()
        return db.query(TestCases).filter(TestCases.testcase_id == testcase_id).first()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))