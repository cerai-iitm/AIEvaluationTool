from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.declarative import declarative_base
from config.settings import settings
import os
import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[4]
config_path = BASE_DIR / "config.json"
local_config_path = Path(__file__).resolve().parent / "config.json"
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[4]
config_path = BASE_DIR / "config.json"
local_config_path = Path(__file__).resolve().parent / "config.json"

try:
    with open(config_path, "r") as f:
        config = json.load(f)
except FileNotFoundError:
    try:
        with open(local_config_path, "r") as f:
            config = json.load(f)
    except FileNotFoundError:
        config = {}
        config = json.load(f)
except FileNotFoundError:
    try:
        with open(local_config_path, "r") as f:
            config = json.load(f)
    except FileNotFoundError:
        config = {}
    
db_cfg = config.get("db", {})
engine_type = db_cfg.get("engine", db_cfg.get("engine_type", "sqlite")).lower()

# def _missing_mariadb_keys() -> list[str]:
#     required_keys = ("host", "port", "user", "password", "database")
#     return [key for key in required_keys if db_cfg.get(key) in (None, "")]


# if engine_type == "mariadb" and _missing_mariadb_keys() and db_cfg.get("file"):
#     engine_type = "sqlite"

if engine_type == "sqlite":
    db_file = db_cfg.get("file", "Auth.db")
    
    # project root: AIEvaluationTool
    project_root = str(BASE_DIR)
    project_root = str(BASE_DIR)
    
    # data folder under project root
    db_folder = os.path.join(project_root, "data")
    os.makedirs(db_folder, exist_ok=True)
    
    # DB file inside the data folder
    db_path = os.path.join(db_folder, db_file)
    
    # Update the SQLALCHEMY_DATABASE_URL
    SQLALCHEMY_DATABASE_URL = f"sqlite:///{db_path}".format(db_path=db_path)

elif engine_type == "mariadb":
    # missing_keys = _missing_mariadb_keys()
    # if missing_keys:
    #     missing = ", ".join(missing_keys)
    #     raise ValueError(f"MariaDB database config is missing required key(s): {missing}")

    SQLALCHEMY_DATABASE_URL = "mariadb+mariadbconnector://{user}:{password}@{host}:{port}/{database}".format(
        user=db_cfg.get("user"),
        password=db_cfg.get("password"),
        host=db_cfg.get("host"),
        port=db_cfg.get("port"),
        database=db_cfg.get("database"),
    )
else: 
    raise ValueError("Unsupported database engine: {engine_type}")

# SQLALCHEMY_DATABASE_URL = f"mysql+mysqlconnector://{settings.DB_USER}:{settings.DB_PASSWORD}@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    # Ensure ORM models are imported so their tables are registered on Base.metadata
    from models import user  # noqa: F401
    Base.metadata.create_all(bind=engine, checkfirst=True)

def seed_users():
    from models.user import User
    from utils.auth import hash_password

    db = SessionLocal()
    try:
        if not db.query(User).first():
            users = [
                User(user_name="admin", email="admin@example.com", password=hash_password("admin123"), role="admin", is_active=True),
                User(user_name="manager", email="manager@example.com", password=hash_password("manager123"), role="manager", is_active=True),
                User(user_name="curator", email="curator@example.com", password=hash_password("curator123"), role="curator", is_active=True),
                User(user_name="viewer", email="viewer@example.com", password=hash_password("viewer123"), role="viewer", is_active=True),
            ]
            db.add_all(users)
            db.commit()
    finally:
        db.close()