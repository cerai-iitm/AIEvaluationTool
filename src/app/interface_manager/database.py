from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from lib.orm.tables import Users
from utils import helpers
# from sqlalchemy.ext.declarative import declarative_base


URL_DATABASE = "mysql+pymysql://root:password@localhost:3306/test"

engine = create_engine(URL_DATABASE)  # done

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)  # probably done 

# Base = declarative_base()                                                                                  


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    Users.__table__.create(bind=engine, checkfirst=True) # done


def seed_users():
    db = SessionLocal()
    if not db.query(Users).first():
        users = [
            Users(user_name="admin", password=helpers.hash_password("admin123"), role="admin", is_active=True),
            Users(user_name="manager", password=helpers.hash_password("manager123"), role="manager", is_active=True),
            Users(user_name="curator", password=helpers.hash_password("curator123"), role="curator", is_active=True),
            Users(user_name="user", password=helpers.hash_password("viewer123"), role="viewer", is_active=True),
        ]
        db.add_all(users)
        db.commit()
    db.close()