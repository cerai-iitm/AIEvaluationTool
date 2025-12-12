import os
from typing import Iterator
from fastapi import Depends, HTTPException
from lib.orm.DB import DB


# from config.settings.settings import AIEVAL_DB_URL 
# _DEFAULT_DB_URL = 'mariadb+mariadbconnector://root:password@localhost:3306/test'

#import argparse 
import json

config_path = os.path.join(os.path.dirname(__file__), "config.json")
try:
    with open(config_path, "r") as f:
        config = json.load(f)
except FileNotFoundError:
    config = {}

db_cfg = config.get("db", {})
engine = db_cfg.get("engine", "sqlite").lower()

if engine == "sqlite":
    db_file = db_cfg.get("file", "AIEvaluationData.db")

    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../.."))
    # print(project_root)

    # data folder under project_root
    db_folder = os.path.join(project_root, "data")
    # print(db_folder)
    os.makedirs(db_folder, exist_ok=True)

    # full path to DB file inside data folder (e.g. data/test.db)
    db_path = os.path.join(db_folder, db_file)
    # print(db_path)

    _DEFAULT_DB_URL = "sqlite:///{db_path}".format(db_path=db_path)
elif engine == "mariadb":
    _DEFAULT_DB_URL = "mariadb+mariadbconnector://{user}:{password}@{host}:{port}/{database}".format(
        user=db_cfg.get("user"),
        password=db_cfg.get("password"),
        host=db_cfg.get("host"),
        port=db_cfg.get("port"),
        database=db_cfg.get("database"),
    )
else:
    raise ValueError("Unsupported database engine: {engine}")    


_db_instance: DB | None = None

def _get_db() -> DB:
    global _db_instance
    if _db_instance is not None:
        return _db_instance
    # db_url = os.getenv("AIEVAL_DB_URL") or _DEFAULT_DB_URL
    db_url = _DEFAULT_DB_URL
    if not db_url:
        raise HTTPException(status_code=500, detail="Database URL not configured (_DEFAULT_DB_URL)")
    _db_instance = DB(db_url=db_url, debug=False)
    return _db_instance

def get_session(db: DB = Depends(_get_db)) -> Iterator[object]:
    session = db.Session()
    try:
        yield session
    finally:
        session.close()