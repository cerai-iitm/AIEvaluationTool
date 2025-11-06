import os
from typing import Iterator
from fastapi import Depends, HTTPException
from lib.orm.DB import DB

_DEFAULT_DB_URL = 'mariadb+mariadbconnector://root:password@localhost:3306/test'

_db_instance: DB | None = None

def get_db() -> DB:
    global _db_instance
    if _db_instance is not None:
        return _db_instance
    db_url = os.getenv("AIEVAL_DB_URL") or _DEFAULT_DB_URL
    if not db_url:
        raise HTTPException(status_code=500, detail="Database URL not configured (AIEVAL_DB_URL)")
    _db_instance = DB(db_url=db_url, debug=False)
    return _db_instance

def get_session(db: DB = Depends(get_db)) -> Iterator[object]:
    session = db.Session()
    try:
        yield session
    finally:
        session.close()