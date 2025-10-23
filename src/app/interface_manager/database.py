from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from lib.orm.tables import user
from sqlalchemy.ext.declarative import declarative_base


URL_DATABASE = "mysql+pymysql://root:password@localhost:3306/test"

engine = create_engine(URL_DATABASE)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()                                                                                  


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    user.__table__.create(bind=engine, checkfirst=True)


def seed_users():
    db = SessionLocal()
    if not db.query(user).first():
        users = [
            user(user_id="ABC001", password=helpers.hash_password("abc@001"), is_active=True),
            user(user_id="DEF001", password=helpers.hash_password("def@001"), is_active=True),
        ]
        db.add_all(users)
        db.commit()
    db.close()