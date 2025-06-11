from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import Column, Integer, Text, DateTime, String, Enum, ForeignKey

class Base(DeclarativeBase):
    """Base class for all ORM models.
    This class serves as a base for all ORM models in the application.
    It inherits from DeclarativeBase, which is a base class for declarative models in SQLAlchemy.
    It can be extended to include common functionality or properties for all models.
    """
    pass

class Prompts(Base):
    """ORM model for the Prompts table.
    This class defines the structure of the Prompts table in the database.
    It inherits from DeclarativeBase, which is a base class for declarative models in SQLAlchemy.
    """
    __tablename__ = 'Prompts'
    
    prompt_id = Column(Integer, primary_key=True)
    prompt_string = Column(Text, nullable=False)
    system_prompt = Column(Text, nullable=True)
    lang_id = Column(Integer, ForeignKey('Languages.lang_id'), nullable=False)    # Foreign key to Languages

class Languages(Base):
    """ORM model for the Languages table.
    This class defines the structure of the Languages table in the database.
    """
    __tablename__ = 'Languages'
    
    lang_id = Column(Integer, primary_key=True)
    lang_name = Column(String(255), nullable=False)

class Domains(Base):
    """ORM model for the Domains table.
    This class defines the structure of the Domains table in the database.
    """
    __tablename__ = 'Domains'
    
    domain_id = Column(Integer, primary_key=True)   
    domain_name = Column(String(255), nullable=False)

class Metrics(Base):
    """ORM model for the Metrics table.
    This class defines the structure of the Metrics table in the database.
    """
    __tablename__ = 'Metrics'
    
    metric_id = Column(Integer, primary_key=True)
    metric_name = Column(String(255), nullable=False)
    metric_source = Column(String(255), nullable=True)
    domain_id = Column(Integer, nullable=False)  # Foreign key to Domains
    metric_benchmark = Column(String(255), nullable=True)

class Responses(Base):
    """ORM model for the Responses table.
    This class defines the structure of the Responses table in the database.
    """
    __tablename__ = 'Responses'
    
    response_id = Column(Integer, primary_key=True)
    response_text = Column(Text, nullable=False)
    response_type = Column(Enum('GT', 'GTDesc', 'NA'), nullable=False)  # GT: Ground Truth, GTDesc: Ground Truth Description, NA: Not Applicable
    prompt_id = Column(Integer, nullable=False) # Foreign key to Prompts
    lang_id = Column(Integer, nullable=False) # Foreign key to Languages

class TestCases(Base):
    """ORM model for the TestCases table.
    This class defines the structure of the TestCases table in the database.
    """
    __tablename__ = 'TestCases'
    
    test_case_id = Column(Integer, primary_key=True)
    test_case_name = Column(String(255), nullable=False)
    prompt_id = Column(Integer, nullable=False) # Foreign key to Prompts
    response_id = Column(Integer, nullable=False) # Foreign key to Responses

class TestPlans(Base):
    """ORM model for the TestPlans table.
    This class defines the structure of the TestPlans table in the database.
    """
    __tablename__ = 'TestPlans'
    
    plan_id = Column(Integer, primary_key=True)
    plan_name = Column(String(255), nullable=False)
    plan_description = Column(Text, nullable=True)  # Optional description for the test plan

class TargetSessions(Base):
    """ORM model for the TargetSessions table.
    This class defines the structure of the TargetSessions table in the database.
    """
    __tablename__ = 'TargetSessions'
    
    session_id = Column(Integer, primary_key=True)
    session_name = Column(String(255), nullable=False)  # Name of the session
    target_id = Column(Integer, nullable=False)  # Foreign key to Targets

class Targets(Base):
    """ORM model for the Targets table.
    This class defines the structure of the Targets table in the database.
    """
    __tablename__ = 'Targets'
    
    target_id = Column(Integer, primary_key=True)
    target_name = Column(String(255), nullable=False)  # Name of the target
    target_type = Column(String(100), nullable=False)  # Type of the target
    target_url = Column(String(255), nullable=False)  # URL of the target (if applicable)
    domain_id = Column(Integer, nullable=False)  # Foreign key to Domains

class Conversations(Base):
    """ORM model for the Conversations table.
    This class defines the structure of the Conversations table in the database.
    """
    __tablename__ = 'Conversations'
    
    conversation_id = Column(Integer, primary_key=True)
    target_id = Column(Integer, nullable=False)  # Foreign key to Targets
    testcase_id = Column(Integer, nullable=False)  # Foreign key to TestCases
    agent_response = Column(Text, nullable=True)  # Name of the conversation
    prompt_ts = Column(DateTime, nullable=True)  # Start timestamp of the conversation
    response_ts = Column(DateTime, nullable=True)  # End timestamp of the conversation

class MetricTestCaseMapping(Base):
    """ORM model for the MetricTestCaseMapping table.
    This class defines the structure of the MetricTestCaseMapping table in the database.
    It maps metrics to test cases.
    """
    __tablename__ = 'MetricTestCaseMapping'
    
    mapping_id = Column(Integer, primary_key=True)
    testcase_id = Column(Integer, nullable=False)  # Foreign key to TestCases
    metric_id = Column(Integer, nullable=False)  # Foreign key to Metrics

class TargetLanguages(Base):
    """ORM model for the TargetLanguages table.
    This class defines the structure of the TargetLanguages table in the database.  
    It maps targets to languages.
    """
    __tablename__ = 'TargetLanguages'
    
    target_lang_id = Column(Integer, primary_key=True)
    target_id = Column(Integer, nullable=False)  # Foreign key to Targets
    lang_id = Column(Integer, nullable=False)  # Foreign key to Languages

class TestPlanMetricMapping(Base):
    """ORM model for the TestPlanMetricMapping table.
    This class defines the structure of the TestPlanMetricMapping table in the database.
    It maps test plans to metrics.
    """
    __tablename__ = 'TestPlanMetricMapping'
    
    mapping_id = Column(Integer, primary_key=True)
    plan_id = Column(Integer, nullable=False)  # Foreign key to TestPlans
    metric_id = Column(Integer, nullable=False)  # Foreign key to Metrics

class TestRuns(Base):
    """ORM model for the TestRuns table.
    This class defines the structure of the TestRuns table in the database.
    It stores information about test runs, including their status and timestamps.
    """
    __tablename__ = 'TestRuns'
    
    run_id = Column(Integer, primary_key=True)
    target_id = Column(Integer, nullable=False)  # Foreign key to Targets   
    session_id = Column(Integer, nullable=False)  # Foreign key to TargetSessions
    start_ts = Column(DateTime, nullable=True)  # Start timestamp of the test run
    end_ts = Column(DateTime, nullable=True)  # End timestamp of the test run
    status = Column(Enum('NEW', 'RUNNING', 'COMPLETED', 'FAILED'), nullable=False)  # Status of the test run

class TestRunDetails(Base):
    """ORM model for the TestRunDetails table.
    This class defines the structure of the TestRunDetails table in the database.
    It stores detailed information about each test run, including metrics and results.
    """
    __tablename__ = 'TestRunDetails'
    
    detail_id = Column(Integer, primary_key=True)
    run_id = Column(Integer, nullable=False)  # Foreign key to TestRuns
    plan_id = Column(Integer, nullable=False)  # Foreign key to TestPlans
    plan_status = Column(Enum('NEW', 'RUNNING', 'COMPLETED', 'FAILED'), nullable=False)  # Status of the test plan in the run
    metric_id = Column(Integer, nullable=False)  # Foreign key to Metrics
    metric_status = Column(Enum('NEW', 'RUNNING', 'COMPLETED', 'FAILED'), nullable=False)  # Status of the metric in the run
    testcase_id = Column(Integer, nullable=False)  # Foreign key to TestCases
    testcase_status = Column(Enum('NEW', 'RUNNING', 'COMPLETED', 'FAILED'), nullable=False)  # Status of the test case in the run