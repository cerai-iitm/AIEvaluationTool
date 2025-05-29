from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text, Enum
import enum
from sqlalchemy.orm import declarative_base
from dotenv import load_dotenv
import os

load_dotenv()

print(os.getenv("PG_URL"))

#postgresql+psycopg2://user:password@host:port/dbname[?key=value&key=value...]
engine = create_engine(os.getenv("PG_URL"))

Base = declarative_base()

class Metric(Base):
    __tablename__ = 'metrics'

    id = Column(Integer, primary_key=True, autoincrement=True)
    type = Column(String, nullable=False)
    mapped_benchmark = Column(String, nullable=False)
    source = Column(Text, nullable=False)
    metric = Column(String, nullable=False)


class MetricOperation(Base):
    __tablename__ = 'metric_operations'

    id = Column(Integer, primary_key=True, autoincrement=True)
    metric_operation_name = Column(String, nullable=False)


class LanguageEnum(enum.Enum):
    ENGLISH = "english"
    TAMIL = "tamil"
    HINDI = "hindi"
    BENGALI = "bengali"
    GUJURATI = "gujurati"

class Prompt(Base):
    __tablename__ = 'prompts'

    id = Column(Integer, primary_key=True, autoincrement=True)
    system_prompt = Column(String, nullable=False)
    prompt = Column(Text, nullable=False)
    prompt_type = Column(String, nullable=False)


Base.metadata.create_all(bind=engine)