from sqlalchemy.orm import DeclarativeBase, relationship
from sqlalchemy import Column, Integer, Text, DateTime, String, Enum, ForeignKey, Float, Boolean
from sqlalchemy_utils import ChoiceType
from datetime import datetime
import uuid

class Base(DeclarativeBase):
    """Base class for all ORM models.
    This class serves as a base for all ORM models in the application.
    It inherits from DeclarativeBase, which is a base class for declarative models in SQLAlchemy.
    It can be extended to include common functionality or properties for all models.
    """
    __abstract__ = True

class Prompts(Base):
    """ORM model for the Prompts table.
    This class defines the structure of the Prompts table in the database.
    It inherits from DeclarativeBase, which is a base class for declarative models in SQLAlchemy.
    """
    __tablename__ = 'Prompts'
    
    prompt_id = Column(Integer, primary_key=True)
    user_prompt = Column(Text, nullable=False)
    system_prompt = Column(Text, nullable=True)
    lang_id = Column(Integer, ForeignKey('Languages.lang_id'), nullable=False)    # Foreign key to Languages
    domain_id = Column(Integer, ForeignKey('Domains.domain_id'), nullable=False)  # Foreign key to Domains
    hash_value = Column(String(100), nullable=False, unique=True)  # Hash value for the prompt
    test_cases = relationship("TestCases", back_populates="prompt")  # Relationship to TestCases
    domain = relationship("Domains", back_populates="prompts")  # Relationship to Domains
    lang = relationship("Languages", back_populates="prompts")
    responses = relationship("Responses", back_populates="prompt")

class LLMJudgePrompts(Base):
    """ORM model for the LLMJudgePrompts table.
    This class defines the structure of the LLMJudgePrompts table in the database.
    It inherits from DeclarativeBase, which is a base class for declarative models in SQLAlchemy.
    """
    __tablename__ = 'LLMJudgePrompts'
    
    prompt_id = Column(Integer, primary_key=True)
    prompt = Column(Text, nullable=False)  # Text of the judge prompt
    lang_id = Column(Integer, ForeignKey('Languages.lang_id'), nullable=False)  # Foreign key to Languages
    hash_value = Column(String(100), nullable=False, unique=True)  # Hash value for the prompt
    test_cases = relationship("TestCases", back_populates="judge_prompt")  # Relationship to TestCases
    lang = relationship("Languages", back_populates="judge_prompts")

class Strategies(Base):
    """ORM model for the Strategies table.
    This class defines the structure of the Strategies table in the database.
    """
    __tablename__ = 'Strategies'
    
    strategy_id = Column(Integer, primary_key=True)
    strategy_name = Column(String(255), nullable=False, unique=True)  # Name of the strategy
    strategy_description = Column(Text, nullable=True)  # Optional description of the strategy

    testcase = relationship("TestCases", back_populates="strategy")  # Relationship to TestCases

class Languages(Base):
    """ORM model for the Languages table.
    This class defines the structure of the Languages table in the database.
    """
    __tablename__ = 'Languages'
    
    lang_id = Column(Integer, primary_key=True)
    lang_name = Column(String(255), nullable=False)
    prompts = relationship("Prompts", back_populates="lang")
    judge_prompts = relationship("LLMJudgePrompts", back_populates="lang")
    responses = relationship("Responses", back_populates="lang")
    targets = relationship("Targets", secondary="TargetLanguages", back_populates="langs")

class Domains(Base):
    """ORM model for the Domains table.
    This class defines the structure of the Domains table in the database.
    """
    __tablename__ = 'Domains'
    
    domain_id = Column(Integer, primary_key=True)   
    domain_name = Column(String(255), nullable=False)
    prompts = relationship("Prompts", back_populates="domain")  # Relationship to Prompts
    targets = relationship("Targets", back_populates="domain")

class Responses(Base):
    """ORM model for the Responses table.
    This class defines the structure of the Responses table in the database.
    """
    __tablename__ = 'Responses'
    
    response_id = Column(Integer, primary_key=True)
    response_text = Column(Text, nullable=False)
    response_type = Column(Enum('GT', 'GTDesc', 'NA'), nullable=False)  # GT: Ground Truth, GTDesc: Ground Truth Description, NA: Not Applicable
    prompt_id = Column(Integer, ForeignKey('Prompts.prompt_id'), nullable=False) # Foreign key to Prompts
    lang_id = Column(Integer, ForeignKey('Languages.lang_id'), nullable=False) # Foreign key to Languages
    hash_value = Column(String(100), nullable=False, unique=True)  # Hash value for the prompt
    test_cases = relationship("TestCases", back_populates="response")  # Relationship to TestCases
    prompt = relationship("Prompts", back_populates="responses")
    lang = relationship("Languages", back_populates="responses")

class TestCases(Base):
    """ORM model for the TestCases table.
    This class defines the structure of the TestCases table in the database.
    """
    __tablename__ = 'TestCases'
    
    testcase_id = Column(Integer, primary_key=True)
    testcase_name = Column(String(255), nullable=False, unique=True)  # Unique name for the test case
    prompt_id = Column(Integer, ForeignKey('Prompts.prompt_id'), nullable=False) # Foreign key to Prompts
    response_id = Column(Integer, ForeignKey('Responses.response_id'), nullable=True) # Foreign key to Responses
    strategy_id = Column(Integer, ForeignKey('Strategies.strategy_id'), nullable=False)  # Foreign key to Strategies
    judge_prompt_id = Column(Integer, ForeignKey('LLMJudgePrompts.prompt_id'), nullable=True)  # Foreign key to LLMJudgePrompts
    metrics = relationship("Metrics", secondary="MetricTestCaseMapping", back_populates="cases")
    prompt = relationship("Prompts", back_populates="test_cases")
    response = relationship("Responses", back_populates="test_cases")
    judge_prompt = relationship("LLMJudgePrompts", back_populates="test_cases")
    run_details = relationship("TestRunDetails", back_populates="testcase")  # Relationship to TestRunDetails
    strategy = relationship("Strategies", back_populates="testcase")  # Relationship to Strategies

class TestPlans(Base):
    """ORM model for the TestPlans table.
    This class defines the structure of the TestPlans table in the database.
    """
    __tablename__ = 'TestPlans'
    
    plan_id = Column(Integer, primary_key=True)
    plan_name = Column(String(255), nullable=False, unique=True)  # Unique name for the test plan
    plan_description = Column(Text, nullable=True)  # Optional description for the test plan
    metrics = relationship("Metrics", secondary="TestPlanMetricMapping", back_populates="plans")
    run_details = relationship("TestRunDetails", back_populates="plan")  # Relationship to TestRuns

class Metrics(Base):
    """ORM model for the Metrics table.
    This class defines the structure of the Metrics table in the database.
    """
    __tablename__ = 'Metrics'
    
    metric_id = Column(Integer, primary_key=True)
    metric_name = Column(String(255), nullable=False, unique=True)
    metric_description = Column(Text, nullable=True)  # Optional description for the metric
    metric_source = Column(String(255), nullable=True)
    domain_id = Column(Integer, ForeignKey('Domains.domain_id'), nullable=False)  # Foreign key to Domains
    metric_benchmark = Column(String(255), nullable=True)
    plans = relationship("TestPlans", secondary="TestPlanMetricMapping", back_populates="metrics")
    cases = relationship("TestCases", secondary="MetricTestCaseMapping", back_populates="metrics")
    run_details = relationship("TestRunDetails", back_populates="metric")  # Relationship to TestRunDetails

class TestPlanMetricMapping(Base):
    """ORM model for the TestPlanMetricMapping table.
    This class defines the structure of the TestPlanMetricMapping table in the database.
    It maps test plans to metrics.
    """
    __tablename__ = 'TestPlanMetricMapping'
    
    mapping_id = Column(Integer, primary_key=True)
    plan_id = Column(Integer, ForeignKey('TestPlans.plan_id'), nullable=False)  # Foreign key to TestPlans
    metric_id = Column(Integer, ForeignKey('Metrics.metric_id'), nullable=False)  # Foreign key to Metrics

class MetricTestCaseMapping(Base):
    """ORM model for the MetricTestCaseMapping table.
    This class defines the structure of the MetricTestCaseMapping table in the database.
    It maps metrics to test cases.
    """
    __tablename__ = 'MetricTestCaseMapping'
    
    mapping_id = Column(Integer, primary_key=True)
    testcase_id = Column(Integer, ForeignKey('TestCases.testcase_id'), nullable=False)  # Foreign key to TestCases
    metric_id = Column(Integer, ForeignKey('Metrics.metric_id'), nullable=False)  # Foreign key to Metrics

class Targets(Base):
    """ORM model for the Targets table.
    This class defines the structure of the Targets table in the database.
    """
    __tablename__ = 'Targets'
    
    target_id = Column(Integer, primary_key=True)
    target_name = Column(String(255), nullable=False, unique=True)  # Name of the target (Also the AI Agent name in WA targets)
    target_type = Column(Enum('WhatsApp', 'WebApp', 'API'), nullable=False, index=True)  # Type of the target
    target_description = Column(Text, nullable=True)  # Description of the target
    target_url = Column(String(255), nullable=False)  # URL of the target (if applicable)
    domain_id = Column(Integer, ForeignKey('Domains.domain_id'), nullable=False)  # Foreign key to Domains

    langs = relationship("Languages", secondary="TargetLanguages", back_populates="targets")
    domain = relationship("Domains", back_populates="targets")
    runs = relationship("TestRuns", back_populates="target")  # Relationship to TargetSessions
    conversations = relationship("Conversations", back_populates="target")  # Relationship to Conversations

class Conversations(Base):
    """ORM model for the Conversations table.
    This class defines the structure of the Conversations table in the database.
    """
    __tablename__ = 'Conversations'
    
    conversation_id = Column(Integer, primary_key=True)
    target_id = Column(Integer, ForeignKey('Targets.target_id'), nullable=False)  # Foreign key to Targets
    detail_id = Column(Integer, ForeignKey('TestRunDetails.detail_id'), nullable=False)  # Foreign key to TestRunDetails
    agent_response = Column(Text, nullable=True)  # AI agent response of the conversation
    prompt_ts = Column(DateTime, nullable=True)  # Start timestamp of the conversation
    response_ts = Column(DateTime, nullable=True)  # End timestamp of the conversation
    evaluation_score = Column(Float, nullable=True)  # The evaluation score assigned to the agent response
    evaluation_reason = Column(Text, nullable=True)  # The reason or explanation for the evaluation score   
    evaluation_ts = Column(DateTime, nullable=True)  # Timestamp when the evaluation was performed

    target = relationship("Targets", back_populates="conversations")  # Relationship to Targets
    detail = relationship("TestRunDetails", back_populates="conversation")  # Relationship to TestRunDetails

class TargetLanguages(Base):
    """ORM model for the TargetLanguages table.
    This class defines the structure of the TargetLanguages table in the database.  
    It maps targets to languages.
    """
    __tablename__ = 'TargetLanguages'
    
    target_lang_id = Column(Integer, primary_key=True)
    target_id = Column(Integer, ForeignKey('Targets.target_id'), nullable=False)  # Foreign key to Targets
    lang_id = Column(Integer, ForeignKey('Languages.lang_id'), nullable=False)  # Foreign key to Languages

class TestRuns(Base):
    """ORM model for the TestRuns table.
    This class defines the structure of the TestRuns table in the database.
    It stores information about test runs, including their status and timestamps.
    """
    __tablename__ = 'TestRuns'
    
    run_id = Column(Integer, primary_key=True)
    run_name = Column(String(255), nullable=False, unique=True)  # Name of the test run
    target_id = Column(Integer, ForeignKey('Targets.target_id'), nullable=False)  # Foreign key to Targets   
    #session_id = Column(Integer, ForeignKey('TargetSessions.session_id'), nullable=False)  # Foreign key to TargetSessions
    start_ts = Column(DateTime, nullable=True)  # Start timestamp of the test run
    end_ts = Column(DateTime, nullable=True)  # End timestamp of the test run
    status = Column(Enum('NEW', 'RUNNING', 'COMPLETED', 'FAILED'), nullable=False)  # Status of the test run

    run_details = relationship("TestRunDetails", back_populates="run")  # Relationship to TestRunDetails
    target = relationship("Targets", back_populates="runs")  # Relationship to Targets

class TestRunDetails(Base):
    """ORM model for the TestRunDetails table.
    This class defines the structure of the TestRunDetails table in the database.
    It stores detailed information about each test run, including metrics and results.
    """
    __tablename__ = 'TestRunDetails'
    
    detail_id = Column(Integer, primary_key=True)
    run_id = Column(Integer, ForeignKey('TestRuns.run_id'), nullable=False)  # Foreign key to TestRuns
    plan_id = Column(Integer, ForeignKey('TestPlans.plan_id'), nullable=False)  # Foreign key to TestPlans
    metric_id = Column(Integer, ForeignKey('Metrics.metric_id'), nullable=False)  # Foreign key to Metrics
    testcase_id = Column(Integer, ForeignKey('TestCases.testcase_id'), nullable=False)  # Foreign key to TestCases
    testcase_status = Column(Enum('NEW', 'RUNNING', 'COMPLETED', 'FAILED'), nullable=False)  # Status of the test case in the run

    run = relationship("TestRuns", back_populates="run_details")
    metric = relationship("Metrics", back_populates="run_details")
    plan = relationship("TestPlans", back_populates="run_details")
    testcase = relationship("TestCases", back_populates="run_details")
    conversation = relationship("Conversations", back_populates="detail")  # Relationship to Conversations
