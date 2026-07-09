from sqlalchemy import create_engine, inspect
# from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from config import helpers
from models import user
from fastapi import Depends, HTTPException, status, Header
# from jose import jwt, JWTError
from config.settings import settings
from typing import Optional
import os
import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[4]
config_path = BASE_DIR / "config.json"

try:
    with open(config_path, "r") as f:
        config = json.load(f)
except FileNotFoundError:
    config = {}

# # DB file in data folder
# db_path = os.path.join(db_folder, "TDMS.db") 

# SQLALCHEMY_DATABASE_URL = f"sqlite:///{db_path}"

db_cfg = config.get("db", {})
engine_type = db_cfg.get("engine", "sqlite").lower()

if engine_type == "sqlite":
    db_file = db_cfg.get("file", "TDMS.db")
    
    # project root: AIEvaluationTool
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../.."))

    # data folder under project root
    db_folder = os.path.join(project_root, "data")
    os.makedirs(db_folder, exist_ok=True)
    
    # DB file inside the data folder
    db_path = os.path.join(db_folder, db_file)
    
    # Update the SQLALCHEMY_DATABASE_URL
    SQLALCHEMY_DATABASE_URL = f"sqlite:///{db_path}".format(db_path=db_path)
    
    # # Re-create the engine with the new URL
    # engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
    # SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
elif engine_type == "mariadb":
    SQLALCHEMY_DATABASE_URL = "mariadb+mariadbconnector://{user}:{password}@{host}:{port}/{database}".format(
        user=db_cfg.get("user"),
        password=db_cfg.get("password"),
        host=db_cfg.get("host"),
        port=db_cfg.get("port"),
        database=db_cfg.get("database"),
    )
    engine = create_engine(SQLALCHEMY_DATABASE_URL)
else: 
    raise ValueError("Unsupported database engine: {engine_type}")
    
    
# engine = create_engine( 
#     SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
_schema_initialized = False


def ensure_db_ready() -> None:
    global _schema_initialized

    if _schema_initialized:
        return

    inspector = inspect(engine)
    if not inspector.has_table(user.Users.__tablename__):
        user.Base.metadata.create_all(bind=engine, checkfirst=True)

    with SessionLocal() as db:
        has_users = db.query(user.Users.user_id).first() is not None
        if not has_users:
            users = [
                user.Users(user_name="admin", email="admin@example.com", password=helpers.hash_password("admin123"), role="admin", is_active=True),
                user.Users(user_name="manager", email="manager@example.com", password=helpers.hash_password("manager123"), role="manager", is_active=True),
                user.Users(user_name="curator", email="curator@example.com", password=helpers.hash_password("curator123"), role="curator", is_active=True),
                user.Users(user_name="viewer", email="viewer@example.com", password=helpers.hash_password("viewer123"), role="viewer", is_active=True),
            ]
            db.add_all(users)
            db.commit()

    _schema_initialized = True



def get_db():
    ensure_db_ready()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


from utils.auth import get_current_user

def init_db():
    ensure_db_ready()

# def init_db():
#     # Create all tables based on the Base metadata.
#     from app.models.user import Users
#     Base.metadata.create_all(bind=engine, checkfirst=True)


def seed_users():
    ensure_db_ready()
