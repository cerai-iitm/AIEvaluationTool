from sqlalchemy import create_engine
# from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from config import helpers
from models import user


SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine( 
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    # Create all tables based on the Base metadata.
    user.Base.metadata.create_all(bind=engine, checkfirst=True)

# def init_db():
#     # Create all tables based on the Base metadata.
#     from app.models.user import Users
#     Base.metadata.create_all(bind=engine, checkfirst=True)


def seed_users():
    # Local import to avoid circular imports at module import time
    # from app.models.user import Users

    db = SessionLocal()
    try:
        if not db.query(user.Users).first():
            users = [
                user.Users(user_name="admin", password=helpers.hash_password("admin123"), role="admin", is_active=True),
                user.Users(user_name="manager", password=helpers.hash_password("manager123"), role="manager", is_active=True),
                user.Users(user_name="curator", password=helpers.hash_password("curator123"), role="curator", is_active=True),
                user.Users(user_name="user", password=helpers.hash_password("viewer123"), role="viewer", is_active=True),
            ]
            db.add_all(users)
            db.commit()
    finally:
        db.close()