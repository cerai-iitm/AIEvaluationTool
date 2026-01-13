from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker, scoped_session, joinedload
from sqlalchemy.exc import IntegrityError
from typing import List, Optional, Union
from  sqlalchemy.sql.expression import func
import sys
import os
import logging
import random
import hashlib

from datetime import datetime

# setup the relative import path for data module.
sys.path.append(os.path.dirname(__file__) + '/..')

from data import Prompt, Language, Domain, Response, TestCase, TestPlan, \
    Strategy, Metric, LLMJudgePrompt, Target, Conversation, Run, RunDetail
from .tables import Base, Languages, Domains, Metrics, Responses, TestCases, \
    TestPlans, Prompts, Strategies, LLMJudgePrompts, Targets, Conversations, \
        TestRuns, TestRunDetails, TestPlanMetricMapping
from lib.utils import get_logger

from jose import jwt, JWTError
from fastapi import Depends, Header

sys.path.append(os.path.dirname(__file__) + "/../../app/TDMS/back-end")
from config import settings


class DB:    
    """
    Database connection and session management class.
    This class provides methods to create a database engine, session, and manage the connection lifecycle.
    It uses SQLAlchemy for ORM and supports MariaDB as the database backend.
    """

    def __init__(self, db_url: str, debug:bool, pool_size:int = 5, max_overflow:int = 10, loglevel=logging.DEBUG):
        """
        Initializes the DB instance with the provided database URL and host.
        
        Args:
            db_url (str): The database URL for connecting to the MariaDB database.
            debug (bool): If True, enables debug mode for SQLAlchemy.
            pool_size (int): The size of the connection pool.
            max_overflow (int): The maximum number of connections that can be created beyond the pool size.
        """
        self.db_url = db_url
        self.engine = create_engine(self.db_url, echo=debug, pool_size=pool_size, max_overflow=max_overflow)
        # Create all tables in the database
        # This will create the tables defined in the ORM models if they do not exist.
        Base.metadata.create_all(self.engine)
        # Create a scoped session to manage database sessions
        # A scoped session is a thread-safe session that can be used across multiple threads.
        self.Session = scoped_session(sessionmaker(bind=self.engine))

        # Set up logging
        self.logger = get_logger(__name__, loglevel=loglevel)

    @property
    def languages(self) -> List[Language]:
        """
        Fetches all languages from the database.
        
        Returns:
            List[Language]: A list of Language objects or None if no languages are found.
        """
        with self.Session() as session:
            sql = select(Languages)
            #return [Language(name=lang.lang_name, code=lang.lang_id) for lang in session.query(Languages).all()]
            return [Language(name=getattr(lang, 'lang_name'), code=getattr(lang, 'lang_id')) for lang in session.query(Languages).all()]
        # If no languages are found, return None
        return None
    
    @property
    def domains(self) -> List[Domain]:
        """
        Fetches all domains from the database.
        
        Returns:
            List[Domain]: A list of Domain objects or None if no domains are found.
        """
        with self.Session() as session:
            sql = select(Domains)
            return [Domain(name=getattr(domain, 'domain_name'), code=getattr(domain, 'domain_id')) for domain in session.query(Domains).all()]
        return None
    
    @property
    def strategies(self) -> List[Strategy]:
        """
        Fetches all strategies from the database.
        
        Returns:
            List[Strategy]: A list of Strategy objects or None if no strategies are found.
        """
        with self.Session() as session:
            self.logger.debug("Fetching all strategies ..")
            return [Strategy(name=getattr(strategy, 'strategy_name'), 
                             description=getattr(strategy, 'strategy_description'),
                             strategy_id=getattr(strategy, 'strategy_id')) for strategy in session.query(Strategies).all()]
        return None
    
    @property
    def plans(self) -> List[TestPlan]:
        """
        Fetches all test plans from the database.
        
        Returns:
            List[TestPlan]: A list of TestPlan objects or None if no plans are found.
        """
        with self.Session() as session:
            self.logger.debug("Fetching all test plans ..")
            return [TestPlan(plan_name=getattr(plan, 'plan_name'), 
                             plan_description=getattr(plan, 'plan_description'),
                             plan_id=getattr(plan, 'plan_id')) for plan in session.query(TestPlans).all()]

    @property
    def prompts(self) -> List[Prompt]:
        """
        Fetches all prompts from the database.
        
        Returns:
            List[Prompt]: A list of Prompt objects or None if no prompts are found.
        """
        with self.Session() as session:
            self.logger.debug("Fetching all prompts ..")
            return [Prompt(system_prompt=getattr(prompt, 'system_prompt'), 
                           user_prompt=getattr(prompt, 'user_prompt'),
                           prompt_id=getattr(prompt, 'prompt_id'),
                           domain_id=getattr(prompt, 'domain_id'),
                           lang_id=getattr(prompt, 'lang_id')) for prompt in session.query(Prompts).all()]
        
    @property
    def responses(self) -> List[Response]:
        """
        Fetches all responses from the database.
        
        Returns:
            List[Response]: A list of Response objects or None if no responses are found.
        """
        with self.Session() as session:
            self.logger.debug("Fetching all responses ..")
            return [Response(response_text=getattr(response, 'response_text'), 
                             response_type=getattr(response, 'response_type'),
                             response_id=getattr(response, 'response_id'),
                             prompt_id=getattr(response, 'prompt_id'),
                             lang_id=getattr(response, 'lang_id')) for response in session.query(Responses).all()]
        
    @property
    def llm_judge_prompts(self) -> List[LLMJudgePrompt]:
        """
        Fetches all LLM judge prompts from the database.
        
        Returns:
            List[LLMJudgePrompt]: A list of LLMJudgePrompt objects or None if no judge prompts are found.
        """
        with self.Session() as session:
            self.logger.debug("Fetching all LLM judge prompts ..")
            return [LLMJudgePrompt(prompt=getattr(judge_prompt, 'prompt'),
                                   lang_id=getattr(judge_prompt, 'lang_id'),
                                   prompt_id=getattr(judge_prompt, 'prompt_id')) for judge_prompt in session.query(LLMJudgePrompts).all()]

    @property
    def testcases(self) -> List[TestCase]:
        """
        Fetches all test cases from the database.
        
        Returns:
            List[TestCase]: A list of TestCase objects or None if no test cases are found.
        """
        with self.Session() as session:
            self.logger.debug("Fetching all test cases ..")
            # Fetch all test cases from the database
            testcases:List[TestCase] = []
            for testcase in session.query(TestCases).all():
                name=getattr(testcase, 'testcase_name')
                testcase_id=getattr(testcase, 'testcase_id')

                prompt=Prompt(system_prompt=getattr(testcase.prompt, 'system_prompt'), 
                                user_prompt=getattr(testcase.prompt, 'user_prompt'),
                                domain_id=getattr(testcase.prompt, 'domain_id'),
                                lang_id=getattr(testcase.prompt, 'lang_id'))
                strategy=getattr(testcase, 'strategy')
                response=Response(response_text=getattr(testcase.response, 'response_text'), 
                                               response_type=getattr(testcase.response, 'response_type'),
                                               lang_id=getattr(testcase.response, 'lang_id')) if testcase.response else None
                judge_prompt=LLMJudgePrompt(prompt=getattr(testcase.judge_prompt, 'prompt')) if testcase.judge_prompt else None

                test_case = TestCase(name=name,
                                     metric="Unknown",  # Metric is not fetched here, can be set later
                                     prompt=prompt,
                                     strategy=strategy.strategy_name,
                                     response=response,
                                     judge_prompt=judge_prompt,
                                     testcase_id=testcase_id)
                # Add test cases to the list
                testcases.append(test_case)
            self.logger.debug(f"Total test cases fetched: {len(testcases)}")
            # Return the list of test cases
            return testcases            

    @property
    def metrics(self) -> List[Metric]:
        """
        Fetches all metrics from the database.
        
        Returns:
            List[Metric]: A list of Metric objects or None if no metrics are found.
        """
        with self.Session() as session:
            self.logger.debug("Fetching all metrics ..")
            return [Metric(metric_name=getattr(metric, 'metric_name'), 
                           metric_description=getattr(metric, 'metric_description'),
                           metric_id=getattr(metric, 'metric_id'),
                           domain_id=getattr(metric, 'domain_id')) for metric in session.query(Metrics).all()]
        
    @property
    def targets(self) -> List[Target]:
        """
        Fetches all targets from the database.
        
        Returns:
            List[Target]: A list of Target objects or None if no targets are found.
        """
        with self.Session() as session:
            self.logger.debug("Fetching all targets ..")
            targets:List[Target] = []
            for target in session.query(Targets).all():
                target_name = getattr(target, 'target_name')
                target_description = getattr(target, 'target_description')
                target_id = getattr(target, 'target_id')
                target_type = getattr(target, 'target_type')
                target_url = getattr(target, 'target_url')
                target_domain = target.domain.domain_name
                target_langs = [lang.lang_name for lang in target.langs]
                tgt = Target(target_name=target_name,
                             target_type=target_type,
                             target_description=target_description,
                             target_domain=target_domain,
                             target_url=target_url,
                             target_languages=target_langs,
                             target_id=target_id)
                targets.append(tgt)
            
            return targets
        
    @property
    def runs(self) -> List[Run]:
        """
        Fetches all test runs from the database.
        
        Returns:
            List[Run]: A list of Run objects or None if no runs are found.
        """
        with self.Session() as session:
            runs:List[Run] = []
            # Fetch all test runs from the database
            self.logger.debug("Fetching all test runs ..")
            for run in session.query(TestRuns).all():
                run_name = getattr(run, 'run_name')
                run_id = getattr(run, 'run_id')
                run_status = getattr(run, 'status')
                start_ts = getattr(run, 'start_ts')
                start_ts = start_ts.isoformat() if isinstance(start_ts, datetime) else start_ts
                # end_ts can be None if the run is still ongoing
                end_ts = getattr(run, 'end_ts')
                end_ts = end_ts.isoformat() if isinstance(end_ts, datetime) else end_ts
                # Count the number of test run details associated with this run
                run_count = session.query(func.count(TestRunDetails.detail_id)).filter(TestRunDetails.run_id == run_id).scalar()
                target = run.target.target_name
                r = Run(target=target, run_name=run_name, run_id=run_id, status=run_status, start_ts=start_ts, end_ts=end_ts, run_count=run_count)
                runs.append(r)
            return runs
        
    def get_prompt_language_statistics(self) -> dict:
        """
        Fetches statistics of language distribution in prompts.
        
        Returns:
            dict: A dictionary containing language ID and its corresponding prompt count.
        """
        with self.Session() as session:
            self.logger.debug("Fetching prompt language statistics ..")
            sql = select(Prompts.lang_id, func.count(Prompts.prompt_id).label('prompt_count')).group_by(Prompts.lang_id)
            result = session.execute(sql).all()
            stats = {row.lang_id : row.prompt_count for row in result}
            return stats
        
    def get_response_language_statistics(self) -> dict:
        """
        Fetches statistics of language distribution in responses.
        
        Returns:
            dict: A dictionary containing language ID and its corresponding response count.
        """
        with self.Session() as session:
            self.logger.debug("Fetching response language statistics ..")
            sql = select(Responses.lang_id, func.count(Responses.response_id).label('response_count')).group_by(Responses.lang_id)
            result = session.execute(sql).all()
            stats = {row.lang_id : row.response_count for row in result}
            return stats
        
    def get_llm_judge_prompt_language_statistics(self) -> dict:
        """
        Fetches statistics of language distribution in LLM judge prompts.
        
        Returns:
            dict: A dictionary containing language ID and its corresponding judge prompt count.
        """
        with self.Session() as session:
            self.logger.debug("Fetching LLM judge prompt language statistics ..")
            sql = select(LLMJudgePrompts.lang_id, func.count(LLMJudgePrompts.prompt_id).label('judge_prompt_count')).group_by(LLMJudgePrompts.lang_id)
            result = session.execute(sql).all()
            stats = {row.lang_id : row.judge_prompt_count for row in result}
            return stats
    
    def add_or_get_strategy_id(self, strategy_name: str) -> int:
        """
        Fetches the ID of a strategy by its name.
        
        Args:
            strategy_name (str): The name of the strategy to fetch.
        
        Returns:
            Optional[int]: The ID of the strategy if found, otherwise None.
        """
        with self.Session() as session:
            # Check if the strategy already exists in the database.
            existing_strategy = session.query(Strategies).filter_by(strategy_name=strategy_name).first()
            if existing_strategy:
                self.logger.debug(f"Returning the existing strategy ID: {existing_strategy.strategy_id}")
                # Return the ID of the existing strategy
                return getattr(existing_strategy, "strategy_id") 
            self.logger.debug(f"Adding new strategy: {strategy_name}")
            # If the strategy does not exist, create a new one
            new_strategy = Strategies(strategy_name=strategy_name)
            session.add(new_strategy)
            session.commit()
            # Ensure strategy_id is populated
            session.refresh(new_strategy)
            self.logger.debug(f"Strategy added successfully: {new_strategy.strategy_id}")
            # Return the ID of the newly added strategy
            return getattr(new_strategy, "strategy_id")

    def __add_or_get_strategy_custom_id(self, strategy:Strategy, strategy_id: int) -> Optional[Strategies]:
        """
        Fetches the ID of a strategy by its name.

        Args:
            strategy_id (int): The ID of the strategy to fetch.


        Returns:
            Optional[Strategies]: The Strategy object if found, otherwise None.
        """
        with self.Session() as session:
            # Check if the strategy already exists in the database
            existing_strategy = (
                session.query(Strategies).filter_by(strategy_name=strategy.name).first()
            )

            if existing_strategy:
                raise ValueError(f"Strategy name '{strategy.name}' already exists in the database.")
            
            self.logger.debug(f"Adding new strategy with custom strategy_id {strategy_id}: {strategy.name}")

            new_strategy = Strategies(
                strategy_id=strategy_id, 
                strategy_name=strategy.name,
                strategy_description=strategy.description
                )
            session.add(new_strategy)
            session.commit()
            # Ensure strategy_id is populated
            session.refresh(new_strategy)
            self.logger.debug(
                f"Strategy added successfully: {new_strategy.strategy_id}"
            )
            # Return the newly added strategy object
            return new_strategy



    def get_strategy_name(self, strategy_id: int) -> Optional[str]:
        """
        Fetches the name of a strategy by its ID.
        
        Args:
            strategy_id (int): The ID of the strategy to fetch.
        
        Returns:
            Optional[str]: The name of the strategy if found, otherwise None.
        """
        with self.Session() as session:
            sql = select(Strategies).where(Strategies.strategy_id == strategy_id)
            result = session.execute(sql).scalar_one_or_none()
            return getattr(result, "strategy_name", None) if result else None

    def get_strategy_id(self, strategy_id: int) -> Optional[Strategy]:
        """
        Fetches a strategy by its ID.

        Args:
            strategy_id (int): The ID of the strategy to fetch.

        Returns:
            Optional[Strategies]: The Strategys object if found, otherwise None
        """
        with self.Session() as session:
            sql = select(Strategies).where(Strategies.strategy_id == strategy_id)
            result = session.execute(sql).scalar_one_or_none()
            if result is None:
                self.logger.error(f"Strategy with ID {strategy_id} does not exist.")
                return None
            return Strategy(
                name=getattr(result, "strategy_name"),
                description=getattr(result, "strategy_description"),
                strategy_id=getattr(result, "strategy_id"),
            )

    def __add_or_get_language(self, language_name: str) -> Optional[Languages]:
        """
        Adds a new language to the database or fetches it if it already exists.
        
        Args:
            language_name (str): The name of the language to be added or fetched.
        
        Returns:
            Optional[Languages]: The Languages object if found or added, otherwise None.
        """
        try:
            with self.Session() as session:
                # Check if the language already exists in the database.
                existing_language = session.query(Languages).filter_by(lang_name=language_name).first()
                if existing_language:
                    self.logger.debug(f"Returning the existing language: {existing_language.lang_name}")
                    return existing_language
                
                self.logger.debug(f"Adding new language: {language_name}")
                # If the language does not exist, create a new one
                new_language = Languages(lang_name=language_name)
                session.add(new_language)
                session.commit()
                # Ensure lang_id is populated
                session.refresh(new_language)  
                self.logger.debug(f"Language added successfully: {new_language.lang_id}")
                
                return new_language
        except IntegrityError as e:
            self.logger.error(f"Language '{language_name}' already exists. Error: {e}")
            return None

    def add_or_get_language_id(self, language_name: str) -> Optional[int]:
        """
        Adds a new language to the database or fetches its ID if it already exists.
        Args:
            language_name (str): The name of the language to be added or fetched.
        Returns:
            Optional[int]: The ID of the language if found or added, otherwise None.
        """
        lang = self.__add_or_get_language(language_name)
        if lang:
            self.logger.debug(f"Returning the language ID: {lang.lang_id}")
            return getattr(lang, "lang_id")
        # If the language could not be added or fetched, log an error and return None
        self.logger.error(f"Failed to add or get language '{language_name}'.")
        return None

    def __add_or_get_language_custom_Id(self, language_name: str, lang_id: int) -> Optional[Languages]:
        """
        Adds a new language to the database or fetches it if it already exists.
        
        Args:
            language_name (str): The name of the language to be added or fetched.
            lang_id (int): The ID of the language to be added or fetched.
        
        Returns:
            Optional[Languages]: The Languages object if found or added, otherwise None.
        """
        try:
            with self.Session() as session:
                existing_language = session.query(Languages).filter_by(lang_name=language_name).first()
                if existing_language:
                    raise ValueError(f"Language with name '{language_name}' already exists.")

                if existing_language:
                    self.logger.debug(f"Returning the existing language: {existing_language.lang_name}")
                    return existing_language
                
                self.logger.debug(f"Adding new language with custom lang_id {lang_id}: {language_name}")
                new_language = Languages(lang_id=lang_id, lang_name=language_name)
                session.add(new_language)
                session.commit()
                session.refresh(new_language)
                self.logger.debug(f"Language added successfully: {new_language.lang_id}")
                return new_language
        except IntegrityError as e:
            self.logger.error(f"Language '{language_name}' already exists or lang_id conflict. Error: {e}")
            return None


    def get_language_name(self, lang_id: int) -> Optional[str]:
        """
        Fetches the name of a language by its ID.
        
        Args:
            lang_id (int): The ID of the language to fetch.
        
        Returns:
            Optional[str]: The name of the language if found, otherwise None.
        """
        with self.Session() as session:
            sql = select(Languages).where(Languages.lang_id == lang_id)
            result = session.execute(sql).scalar_one_or_none()
            #return result.lang_name if result else None
            return getattr(result, 'lang_name', None) if result else None
        
    def add_or_get_domain_id(self, domain_name: str) -> int:
        """
        Adds a new domain to the database.
        
        Args:
            domain_name (str): The name of the domain to be added.
        
        Returns:
            Optional[int]: The ID of the newly added domain, or None if it already exists.
        """
        try:
            with self.Session() as session:
                # check if the domain already exists in the database.
                existing_domain = session.query(Domains).filter_by(domain_name=domain_name).first()
                if existing_domain:
                    self.logger.debug(f"Returning the existing domain ({domain_name}) ID: {existing_domain.domain_id}")
                    # Return the ID of the existing domain
                    return getattr(existing_domain, "domain_id")
                
                self.logger.debug(f"Adding new domain: {domain_name}")
                new_domain = Domains(domain_name=domain_name)
                session.add(new_domain)
                session.commit()
                # Ensure domain_id is populated
                session.refresh(new_domain)  
                self.logger.debug(f"Domain added successfully: {new_domain.domain_id}")
                
                # Return the ID of the newly added domain
                return getattr(new_domain, "domain_id")
        except IntegrityError as e:
            self.logger.error(f"Domain '{domain_name}' already exists. Error: {e}")
            return -1

    def __add_or_get_domain_custom_Id(self, domain_name: str, domain_id: int) -> Optional[Domains]:
        """
        Adds a new domain to the database or fetches it if it already exists.
        
        Args:
            domain_name (str): The name of the domain to be added or fetched.
            domain_id (int): The ID of the domain to be added or fetched.
        
        Returns:
            Optional[Domains]: The Domains object if found or added, otherwise None.
        """
        try:
            with self.Session() as session:
                existing_domain = session.query(Domains).filter_by(domain_name=domain_name).first()

                if existing_domain:
                    raise ValueError(f"Domain '{domain_name}' already exists.")
                
                self.logger.debug(f"Adding new domain with custom domain_id {domain_id}: {domain_name}")
                new_domain = Domains(domain_id=domain_id, domain_name=domain_name)
                session.add(new_domain)
                session.commit()
                session.refresh(new_domain)
                self.logger.debug(f"Domain added successfully: {new_domain.domain_id}")
                return new_domain
        except IntegrityError as e:
            self.logger.error(f"Domain '{domain_name}' already exists or domain_id conflict. Error: {e}")
            return None

    def get_domain_id(self, domain_name: str) -> Optional[int]:
        """
        Fetches the ID of a domain by its name.
        
        Args:
            domain_name (str): The name of the domain to fetch.
        
        Returns:
            Optional[int]: The ID of the domain if found, otherwise None.
        """
        with self.Session() as session:
            sql = select(Domains).where(Domains.domain_name == domain_name)
            result = session.execute(sql).scalar_one_or_none()
            #return result.domain_id if result else None
            return getattr(result, 'domain_id', None) if result else None

    def get_domain_name(self, domain_id: int) -> Optional[str]:
        """
        Fetches the name of a domain by its ID.
        
        Args:
            domain_id (int): The ID of the domain to fetch.
        
        Returns:
            Optional[str]: The name of the domain if found, otherwise None.
        """
        with self.Session() as session:
            sql = select(Domains).where(Domains.domain_id == domain_id)
            result = session.execute(sql).scalar_one_or_none()
            #return result.domain_name if result else None
            return getattr(result, 'domain_name', None) if result else None
        
    def create_testplan(self, plan_name: str, plan_desc: str = "") -> bool:
        """
        Creates a new test plan in the database.
        
        Args:
            plan_name (str): The name of the test plan.
            plan_desc (str): A description of the test plan.
            kwargs: Additional keyword arguments for future extensibility.
        
        Returns:
            bool: True if the test plan was created successfully, False if it already exists.
        """
        try:
            with self.Session() as session:
                self.logger.debug(f"Creating test plan '{plan_name}' ..")
                new_plan = TestPlans(plan_name=plan_name, plan_description=plan_desc)
                session.add(new_plan)
                session.commit()
                self.logger.debug(f"Test plan '{plan_name}' created successfully.")
                return True
        except IntegrityError as e:
            self.logger.error(f"Test plan '{plan_name}' already exists. Error: {e}")
            return False
        
    def testcase_id2name(self, testcase_id: int) -> Optional[str]:
        """
        Converts a test case ID to its name.
        
        Args:
            testcase_id (int): The ID of the test case.
        
        Returns:
            Optional[str]: The name of the test case if found, otherwise None.
        """
        with self.Session() as session:
            self.logger.debug(f"Fetching test case name for ID '{testcase_id}' ..")
            sql = select(TestCases).where(TestCases.testcase_id == testcase_id)
            result = session.execute(sql).scalar_one_or_none()
            if result is None:
                self.logger.error(f"Test case with ID '{testcase_id}' does not exist.")
                return None
            testcase_name = getattr(result, 'testcase_name', None)
            self.logger.debug(f"Test case name for ID '{testcase_id}' is '{testcase_name}'.")
            return testcase_name
        
    def __strategy_name(self, strategy_id: int) -> str:
        """
        Helper function to get the strategy name from the strategy ID.
        """
        strategy = self.get_strategy_name(strategy_id)
        if strategy:
            return strategy
        
        raise ValueError(f"Strategy with ID {strategy_id} does not exist.")
        
    def fetch_testcase(self, testcase: int|str) -> Optional[TestCase]:
        """
        Fetches a test case by its ID or NAME
        Ex: select user_prompt, Prompts.prompt_id, response_text, Responses.response_id from TestCases left join Responses on TestCases.response_id = Responses.response_id left join Prompts on TestCases.prompt_id = Prompts.prompt_id where TestCases.testcase_name = 'NAME'

        Args:
            testcase (int|str): The ID or NAME of the test case to fetch.
        
        Returns:
            Optional[TestCase]: The TestCase object if found, otherwise None.
        """
        with self.Session() as session:
            self.logger.debug(f"Fetching test case '{testcase}' ..")
            # Construct the SQL query to fetch the test case
            # We will join the Prompts and TestCases tables to get the prompt details
            # and the response details if available.
            #sql = select(Prompts, TestCases).join(TestCases, Prompts.prompt_id == TestCases.prompt_id)
            #sql = session.query(Prompts, Responses, TestCases).join(TestCases, Prompts.prompt_id == TestCases.prompt_id) #.join(Responses, TestCases.response_id == Responses.response_id)
            sql = session.query(Prompts, Responses, TestCases).select_from(TestCases). \
                join(Prompts, TestCases.prompt_id == Prompts.prompt_id). \
                join(Responses, TestCases.response_id == Responses.response_id, isouter=True)
        
            # If testcase is an int, we assume it's the testcase_id
            # If testcase is a str, we assume it's the testcase_name
            if isinstance(testcase, int):
                testcase_id = testcase
                sql = sql.where(TestCases.testcase_id == testcase_id)
            elif isinstance(testcase, str):
                testcase_name = testcase
                sql = sql.where(TestCases.testcase_name == testcase_name)
            else:
                self.logger.error(f"Invalid type for testcase: {type(testcase)}. Expected int or str.")
                return None

            # The query will return the user_prompt, system_prompt, prompt_id, testcase_id,
            # testcase_name, and response_id if available.
            # We will use the scalar_one_or_none() method to get a single result or None
            # if no result is found.
            #result = session.execute(sql).scalar_one_or_none()
            result = sql.one_or_none()
            if result:
                testcase_name = result[2].testcase_name
                testcase_id = result[2].testcase_id
                testcase_strategy = result[2].strategy.strategy_name
                # we will use the first metric associated with the test case
                testcase_metrics = result[2].metrics

                # Create a Prompt object from the result
                prompt = Prompt(prompt_id=getattr(result[0], "prompt_id"),
                                lang_id=getattr(result[0], "lang_id"),
                                domain_id=getattr(result[0], "domain_id"),
                                user_prompt=str(result[0].user_prompt),
                                system_prompt=str(result[0].system_prompt))
                if result[1] is None:
                    response = None
                    response_id = None
                else:
                    # Create a Response object from the result
                    response_id = getattr(result[1], "response_id")
                    response = Response(response_text=str(result[1].response_text),
                                        response_type=result[1].response_type,
                                        response_id = response_id,
                                        prompt_id = result[1].prompt_id,
                                        lang_id=result[1].lang_id,
                                        digest=result[1].hash_value)
                    
                self.logger.debug(f"Test case '{testcase_name}' (ID: {testcase_id}) found with prompt ID: {prompt.prompt_id}")
                return TestCase(name=testcase_name,
                                metric=testcase_metrics[0].metric_name,
                                testcase_id=testcase_id,
                                prompt=prompt,
                                prompt_id=prompt.prompt_id,
                                strategy=testcase_strategy,
                                response=response,
                                response_id=response_id)
            
            self.logger.error(f"Test case '{testcase}' does not exist.")
            return None

    def update_testcase_record(self, testcase_id: int, updates: dict) -> Optional[TestCases]:
        """
        Updates a test case similar to v1 method but using v2 style.
        """
        with self.Session() as session:
            testcase: Optional[TestCases] = (
                session.query(TestCases)
                .options(
                    joinedload(TestCases.prompt).joinedload(Prompts.domain),
                    joinedload(TestCases.response),
                    joinedload(TestCases.strategy),
                    joinedload(TestCases.judge_prompt),
                )
                .filter(TestCases.testcase_id == testcase_id)
                .first()
            )
            if testcase is None:
                return None

            updated = False

            if "testcase_name" in updates and updates["testcase_name"]:
                testcase.testcase_name = updates["testcase_name"]
                updated = True

            if "strategy_name" in updates and updates["strategy_name"]:
                strategy = session.query(Strategies).filter(Strategies.strategy_name == updates["strategy_name"]).first()
                if not strategy:
                    raise ValueError(f"Strategy '{updates['strategy_name']}' not found")
                testcase.strategy_id = strategy.strategy_id
                updated = True

            # Update prompt with hash and reuse logic
            if "user_prompt" in updates or "system_prompt" in updates:
                current_prompt = getattr(testcase, "prompt", None)
                new_user_prompt = updates.get("user_prompt", getattr(current_prompt, "user_prompt", None))
                new_system_prompt = updates.get("system_prompt", getattr(current_prompt, "system_prompt", None))

                # Compute prompt hash same as v1
                prompt_str = f"System: '{new_system_prompt or ''}'\tUser: '{new_user_prompt}'"
                hashing = hashlib.sha1()
                hashing.update(prompt_str.encode("utf-8"))
                new_hash = hashing.hexdigest()

                # Check if prompt with new_hash exists excluding current prompt
                existing_prompt = (
                    session.query(Prompts)
                    .filter(Prompts.hash_value == new_hash)
                    .filter(Prompts.prompt_id != (current_prompt.prompt_id if current_prompt else None))
                    .first()
                )

                if existing_prompt:
                    testcase.prompt_id = existing_prompt.prompt_id
                else:
                    if current_prompt:
                        current_prompt.user_prompt = new_user_prompt
                        current_prompt.system_prompt = new_system_prompt
                        current_prompt.hash_value = new_hash
                    else:
                        # Create new prompt object if none exists
                        prompt_obj = Prompt(
                            user_prompt=new_user_prompt,
                            system_prompt=new_system_prompt,
                            lang_id=Language.autodetect,  # or other fallback
                            domain_id=Domain.general,     # or other fallback
                            hash_value=new_hash
                        )
                        session.add(prompt_obj)
                        session.flush()
                        testcase.prompt_id = prompt_obj.prompt_id
                updated = True

            # Update response text with hash and reuse
            if "response_text" in updates:
                response_text = updates["response_text"]
                if response_text:
                    current_response = getattr(testcase, "response", None)
                    response_type = (
                        getattr(current_response, "response_type", "GT") if current_response else "GT"
                    )
                    response_str = f"Response Text: '{response_text}'\tResponse Type: '{response_type}'"
                    hashing = hashlib.sha1()
                    hashing.update(response_str.encode("utf-8"))
                    new_hash = hashing.hexdigest()

                    existing_response = (
                        session.query(Responses)
                        .filter(Responses.hash_value == new_hash)
                        .filter(Responses.response_id != (current_response.response_id if current_response else None))
                        .first()
                    )

                    if existing_response:
                        testcase.response_id = existing_response.response_id
                    else:
                        if current_response:
                            current_response.response_text = response_text
                            current_response.hash_value = new_hash
                        else:
                            response_obj = Response(
                                response_text=response_text,
                                response_type=response_type,
                                lang_id=Language.autodetect,
                                hash_value=new_hash,
                            )
                            session.add(response_obj)
                            session.flush()
                            testcase.response_id = response_obj.response_id
                    updated = True

            # Update judge prompt with hash and reuse
            if "llm_judge_prompt" in updates:
                judge_prompt_text = updates["llm_judge_prompt"]
                current_judge_prompt = getattr(testcase, "judge_prompt", None)
                if judge_prompt_text:
                    hashing = hashlib.sha1()
                    hashing.update(judge_prompt_text.encode("utf-8"))
                    new_hash = hashing.hexdigest()

                    existing_judge_prompt = (
                        session.query(LLMJudgePrompts)
                        .filter(LLMJudgePrompts.hash_value == new_hash)
                        .filter(LLMJudgePrompts.prompt_id != (current_judge_prompt.prompt_id if current_judge_prompt else None))
                        .first()
                    )

                    if existing_judge_prompt:
                        testcase.judge_prompt_id = existing_judge_prompt.prompt_id
                    else:
                        if current_judge_prompt:
                            current_judge_prompt.prompt = judge_prompt_text
                            current_judge_prompt.hash_value = new_hash
                        else:
                            judge_prompt_obj = LLMJudgePrompts(
                                prompt=judge_prompt_text,
                                lang_id=Language.autodetect,
                                hash_value=new_hash,
                            )
                            session.add(judge_prompt_obj)
                            session.flush()
                            testcase.judge_prompt_id = judge_prompt_obj.prompt_id
                    updated = True
                else:
                    # Clear judge_prompt if blank
                    testcase.judge_prompt_id = None
                    updated = True

            if updated:
                session.commit()
                session.refresh(testcase)
                return testcase
            else:
                session.refresh(testcase)
                return testcase


    def delete_testcase_record(self, testcase_id: int) -> bool:
        """
        Deletes a test case by ID.
        """
        with self.Session() as session:
            testcase = (
                session.query(TestCases)
                .filter(TestCases.testcase_id == testcase_id)
                .first()
            )
            if testcase is None:
                return False
            session.delete(testcase)
            session.commit()
            return True
    
    # def delete_prompt_record(self, prompt_id:int) -> bool:
    #     with self.Session() as session:
    #         prompt = (
    #             session.query(Prompt)
    #             .filter(Prompt.prompt_id == prompt_id)
    #             .first()
    #         )
    #         if prompt is None:
    #             return False
    #         session.delete(prompt)
    #         session.commit()
    #         return True
    
    
    
    def delete_llm_judge_prompt_record(self, llm_judge_prompt_id:int) -> bool:
        with self.Session() as session:
            llm_judge_prompt = (
                session.query(LLMJudgePrompts)
                .filter(LLMJudgePrompts.prompt_id == llm_judge_prompt_id)
                .first()
            )
            if llm_judge_prompt is None:
                return False
            session.delete(llm_judge_prompt)
            session.commit()
            return True
    
    

    def add_testcase(self, testcase: TestCase) -> int:
        """
        Creates a new test case in the database.
        
        Args:
            testcase (TestCase): The TestCase object to be created.
        
        Returns:
            int: The ID of the newly created test case, or -1 if it already exists.
        """
        return self.add_testcase_from_prompt(testcase_name = testcase.name, prompt = testcase.prompt, strategy=testcase.strategy, response = testcase.response)
    
    def add_testcase_from_prompt_id(self, testcase_name: str, prompt_id: int, strategy:int|str, response_id: Optional[int] = None, judge_prompt_id:Optional[int] = None) -> int:
        """
        Creates a new test case in the database using an existing prompt ID.
        
        Args:
            testcase_name (str): The name of the test case.
            prompt_id (int): The ID of the prompt associated with the test case.
            response_id (Optional[int]): The ID of the response associated with the test case.
        
        Returns:
            int: The ID of the newly created test case, or -1 if it already exists.
        """
        strategy_id = strategy
        if isinstance(strategy, str):
            # If strategy is a string, fetch the strategy ID from the database
            strategy_id = self.add_or_get_strategy_id(strategy)
            if strategy_id is None:
                self.logger.error(f"Strategy '{strategy}' does not exist.")
                return -1

        try:
            with self.Session() as session:
                self.logger.debug(f"Creating test case (name:{testcase_name}) ..")

                new_testcase = TestCases(testcase_name=testcase_name,  # Use the test case name
                                         prompt_id=prompt_id,  # Use the provided prompt ID
                                         strategy_id=strategy_id,  # Use the provided strategy ID
                                         judge_prompt_id=judge_prompt_id,  # Use the provided judge prompt ID
                                         response_id=response_id) # Use the provided response ID
                # Add the new test case to the session
                session.add(new_testcase)
                # Commit the session to save all changes
                session.commit()

                self.logger.debug(f"Test case created successfully, name:{new_testcase.testcase_name}, ID:{new_testcase.testcase_id}.")
                return getattr(new_testcase, "testcase_id")
           
        except IntegrityError as e:
            self.logger.error(f"Test case (name:{testcase_name}) already exists. Error: {e}")
            return -1
        
    def add_testcase_from_prompt(self, testcase_name:str, prompt: Prompt, strategy: int|str, response: Optional[Response] = None, judge_prompt: Optional[LLMJudgePrompt] = None) -> int:
        """
        Creates a new test case in the database.
        
        Args:
            prompt (Prompt): The prompt associated with the test case.
            response (Optional[str]): The response associated with the test case.
            kwargs: Additional keyword arguments for future extensibility.
        
        Returns:
            bool: True if the test case was created successfully, False if it already exists.
        """
        strategy_id = strategy
        if isinstance(strategy, str):
            # If strategy is a string, fetch the strategy ID from the database
            strategy_id = self.add_or_get_strategy_id(strategy)
            if strategy_id is None:
                self.logger.error(f"Strategy '{strategy}' does not exist.")
                return -1

        try:
            # Add the prompt to the database and get its ID
            prompt_id = self.add_or_get_prompt(prompt)  
            if prompt_id == -1:
                self.logger.error(f"Prompt '{prompt.user_prompt}' already exists. Cannot create test case.")
                return -1
            
            # If a response is provided, create a Responses object
            response_id = self.add_or_get_response(response, prompt_id) if response else None

            with self.Session() as session:
                self.logger.debug(f"Creating test case (name:{testcase_name}) ..")

                new_testcase = TestCases(testcase_name=testcase_name,  # Use the test case name
                                         prompt_id=prompt_id,  # Use the ID of the added prompt
                                         response_id=response_id, # Use the ID of the added response
                                         strategy_id=strategy_id) 
                # Add the new test case to the session
                session.add(new_testcase)
                # Commit the session to save all changes
                session.commit()

                self.logger.debug(f"Test case created successfully, name:{new_testcase.testcase_name}, ID:{new_testcase.testcase_id}.")
                return getattr(new_testcase, "testcase_id")
           
        except IntegrityError as e:
            self.logger.error(f"Test case (name:{testcase_name}) cannot be added. Error: {e}")
            return -1
        
    def add_or_get_response(self, response: Response, prompt_id:Optional[int] = None) -> int:
        """
        Adds a new response to the database or fetches its ID if it already exists.
        
        Args:
            response (Response): The Response object to be added.
        
        Returns:
            int: The ID of the newly added response, or -1 if it already exists.
        """
        try:
            with self.Session() as session:
                # Check if the response already exists in the database.
                existing_response = session.query(Responses).filter_by(hash_value=response.digest).first()
                if existing_response:
                    self.logger.debug(f"Returning the existing response ID: {existing_response.response_id}")
                    # Return the ID of the existing response
                    return getattr(existing_response, "response_id")
                
                self.logger.debug(f"Adding new response: {response.response_text}")
                # create the orm object for the response to insert into the database table.
                new_response = Responses(response_text=response.response_text, 
                                         response_type=response.response_type,
                                         prompt_id=prompt_id if prompt_id else getattr(response, 'prompt_id'),  # Get the prompt ID
                                         # Get the language ID from kwargs if provided
                                         lang_id=getattr(response, "lang_id", Language.autodetect),  
                                         hash_value=response.digest)
                
                # Add the new response to the session
                session.add(new_response)
                # Commit the session to save the new response
                session.commit()
                # Ensure response_id is populated
                session.refresh(new_response)  

                self.logger.debug(f"Response added successfully: {new_response.response_id}")
                
                # Return the ID of the newly added response
                return getattr(new_response, "response_id")
        except IntegrityError as e:
            # Handle the case where the response already exists
            self.logger.error(f"Response already exists: {response}. Error: {e}")
            return -1

    def __add_or_get_response_by_custom_id(
        self, response: Response, prompt_id: Optional[int], response_id:int
    ) -> Optional[Responses]:
        """
        Adds a new response to the database or fetches its ID if it already exists.

        Args:
            response (Response): The Response object to be added.
            response_id (int): The ID of the response to fetch.

        Returns:
            Optional[Responses]: The Responses object if found, otherwise None.

        """
        try:
            with self.Session() as session:
                existing_response = (
                    session.query(Responses)
                    .filter_by(hash_value=response.digest)
                    .first()
                )
                if existing_response:
                    raise ValueError(f"Response already exists")

                if existing_response:
                    self.logger.debug(
                        f"Returning the existing response ID: {existing_response.response_id}"
                    )

                    return existing_response

                self.logger.debug(f"Adding new response: {response.response_text}")
                # create the orm object for the response to insert into the database table.
                new_response = Responses(
                    response_text=response.response_text,
                    response_type=response.response_type,
                    prompt_id=prompt_id
                    if prompt_id
                    else getattr(response, "prompt_id"),  # Get the prompt ID
                    # Get the language ID from kwargs if provided
                    lang_id=getattr(response, "lang_id", Language.autodetect),
                    hash_value=response.digest,
                    response_id=response_id
                )

                # Add the new response to the session
                session.add(new_response)
                # Commit the session to save the new response
                session.commit()
                # Ensure response_id is populated
                session.refresh(new_response)

                self.logger.debug(
                    f"Response added successfully: {new_response.response_id}"
                )

                # Return the ID of the newly added response
                return new_response
        except IntegrityError as e:
            # Handle the case where the response already exists
            self.logger.error(f"Response already exists: {response}. Error: {e}")
            return None



    def get_response(self, response_id: int) -> Optional[Response]:
        """
        Fetches a response by its ID.
        
        Args:
            response_id (int): The ID of the response to fetch.
        
        Returns:
            Optional[Response]: The Response object if found, otherwise None.
        """
        with self.Session() as session:
            sql = select(Responses).where(Responses.response_id == response_id)
            result = session.execute(sql).scalar_one_or_none()
            if result is None:
                self.logger.error(f"Response with ID '{response_id}' does not exist.")
                return None
            return Response(response_text=str(result.response_text),
                            response_type=str(result.response_type),
                            response_id=getattr(result, 'response_id'),
                            prompt_id=result.prompt_id,
                            lang_id=result.lang_id,
                            digest=result.hash_value)
        
    def get_judge_prompt(self, judge_prompt_id: int) -> Optional[LLMJudgePrompt]:
        """
        Fetches a judge prompt by its ID.
        
        Args:
            judge_prompt_id (int): The ID of the judge prompt to fetch.
        
        Returns:
            Optional[LLMJudgePrompt]: The LLMJudgePrompt object if found, otherwise None.
        """
        with self.Session() as session:
            sql = select(LLMJudgePrompts).where(LLMJudgePrompts.prompt_id == judge_prompt_id)
            result = session.execute(sql).scalar_one_or_none()
            if result is None:
                self.logger.error(f"Judge prompt with ID '{judge_prompt_id}' does not exist.")
                return None
            return LLMJudgePrompt(prompt=str(result.prompt),
                                  lang_id=getattr(result, 'lang_id', Language.autodetect),  # Get the language ID from kwargs if provided
                                  digest=result.hash_value)
        
    # def add_or_get_judge_prompt(self, judge_prompt: LLMJudgePrompt) -> int:
    #     """
    #     Adds a new judge prompt to the database.
        
    #     Args:
    #         judge_prompt (LLMJudgePrompt): The LLMJudgePrompt object to be added.
        
    #     Returns:
    #         int: The ID of the newly added judge prompt, or -1 if it already exists.
    #     """
    #     try:
    #         with self.Session() as session:
    #             # check of the judge prompt already exists in the database.
    #             existing_judge_prompt = session.query(LLMJudgePrompts).filter_by(hash_value=judge_prompt.digest).first()
    #             if existing_judge_prompt:
    #                 # Return the ID of the existing judge prompt
    #                 return getattr(existing_judge_prompt, "prompt_id")
                    
    #             self.logger.debug(f"Adding new judge prompt: {judge_prompt.prompt}")
    #             # create the orm object for the judge prompt to insert into the database table.
    #             new_judge_prompt = LLMJudgePrompts(prompt=judge_prompt.prompt, 
    #                                                lang_id=getattr(judge_prompt, "lang_id", Language.autodetect),  # Get the language ID from kwargs if provided
    #                                                hash_value=judge_prompt.digest)
                
    #             # Add the new judge prompt to the session
    #             session.add(new_judge_prompt)
    #             # Commit the session to save the new judge prompt
    #             session.commit()
    #             # Ensure judge_prompt_id is populated
    #             session.refresh(new_judge_prompt)  

    #             self.logger.debug(f"Judge prompt added successfully: {new_judge_prompt.prompt_id}")
                
    #             # Return the ID of the newly added judge prompt
    #             return getattr(new_judge_prompt, "prompt_id")
    #     except IntegrityError as e:
    #         # Handle the case where the judge prompt already exists
    #         self.logger.error(f"Judge prompt already exists: {judge_prompt}. Error: {e}")
    #         return -1
    
    def get_prompt(self, prompt_id: int) -> Optional[Prompt]:
        """
        Fetches a prompt by its ID.
        
        Args:
            prompt_id (int): The ID of the prompt to fetch.
        
        Returns:
            Optional[Prompt]: The Prompt object if found, otherwise None.
        """
        with self.Session() as session:
            sql = select(Prompts).where(Prompts.prompt_id == prompt_id)
            result = session.execute(sql).scalar_one_or_none()
            if result is None:
                self.logger.error(f"Prompt with ID '{prompt_id}' does not exist.")
                return None
            return Prompt(prompt_id=getattr(result, 'prompt_id'),
                          user_prompt=str(result.user_prompt),
                          system_prompt=str(result.system_prompt),
                          lang_id=getattr(result, 'lang_id'),
                          domain_id=getattr(result, 'domain_id'),
                          hash_value=result.hash_value)
        
    def add_or_update_prompt(self, prompt: Prompt) -> int:
        """
        Adds a new prompt to the database or updates it if it already exists.
        
        Args:
            prompt (Prompt): The Prompt object to be added or updated.
        Returns:
            int: The ID of the newly added or updated prompt.
        """
        try:
            with self.Session() as session:
                # check if the prompt already exists in the database.
                existing_prompt = session.query(Prompts).filter_by(hash_value=prompt.digest).first()
                if existing_prompt:
                    self.logger.debug(f"Updating existing prompt ID: {existing_prompt.prompt_id}")
                    # Update the existing prompt
                    existing_prompt.user_prompt = prompt.user_prompt
                    existing_prompt.system_prompt = prompt.system_prompt
                    existing_prompt.lang_id = prompt.kwargs.get('lang_id', Language.autodetect)
                    existing_prompt.domain_id = prompt.kwargs.get('domain_id', Domain.general)
                    existing_prompt.hash_value = prompt.digest
                    session.commit()
                    return getattr(existing_prompt, "prompt_id")
                
                self.logger.debug(f"Adding new prompt: {prompt.user_prompt}")

                # Default to the default language ID if not provided
                lang_id = prompt.kwargs.get("lang_id", Language.autodetect)  # Get the language ID from kwargs if provided
                domain_id = prompt.kwargs.get("domain_id", Domain.general)  # Get the domain ID from kwargs if provided

                # create the orm object for the prompt to insert into the database table.
                new_prompt = Prompts(user_prompt=prompt.user_prompt, 
                                    system_prompt=prompt.system_prompt, 
                                    lang_id=lang_id,
                                    domain_id=domain_id,
                                    hash_value=prompt.digest)
                
                # Add the new prompt to the session
                session.add(new_prompt)
                # Commit the session to save the new prompt
                session.commit()
                # Ensure prompt_id is populated
                session.refresh(new_prompt)  

                self.logger.debug(f"Prompt added successfully: {new_prompt.prompt_id}")
                
                # Return the ID of the newly added prompt
                return getattr(new_prompt, "prompt_id")
        except IntegrityError as e:
            self.logger.error(f"Error adding or updating prompt: {prompt} Error: {e}")
            return -1

    def add_or_get_prompt(self, prompt: Prompt) -> int:
        """
        Adds a new prompt to the database.
        
        Args:
            prompt (Prompt): The Prompt object to be added.
            returns:
            int: The ID of the newly added prompt, or -1 if it already exists.
        """
        try:
            with self.Session() as session:
                # check of the prompt already exists in the database.
                existing_prompt = session.query(Prompts).filter_by(hash_value=prompt.digest).first()
                if existing_prompt:
                    self.logger.debug(f"Returning the existing prompt ID: {existing_prompt.prompt_id}")
                    # Return the ID of the existing prompt
                    return getattr(existing_prompt, "prompt_id")
                
                self.logger.debug(f"Adding new prompt: {prompt.user_prompt}")

                # Default to the default language ID if not provided
                lang_id = prompt.kwargs.get("lang_id", Language.autodetect)  # Get the language ID from kwargs if provided
                domain_id = prompt.kwargs.get("domain_id", Domain.general)  # Get the domain ID from kwargs if provided

                # create the orm object for the prompt to insert into the database table.
                new_prompt = Prompts(user_prompt=prompt.user_prompt, 
                                    system_prompt=prompt.system_prompt, 
                                    lang_id=lang_id,
                                    domain_id=domain_id,
                                    hash_value=prompt.digest)
                
                # Add the new prompt to the session
                session.add(new_prompt)
                # Commit the session to save the new prompt
                session.commit()
                # Ensure prompt_id is populated
                session.refresh(new_prompt)  

                self.logger.debug(f"Prompt added successfully: {new_prompt.prompt_id}")
                
                # Return the ID of the newly added prompt
                return getattr(new_prompt, "prompt_id")
        except IntegrityError as e:
            # Handle the case where the prompt already exists
            self.logger.error(f"Prompt already exists: {prompt} Error: {e}")
            return -1

    def __add_or_get_prompt_custom_Id(self, prompt: Prompt, prompt_id: int, domain_id: int, lang_id: int) -> Optional[Prompts]:
        """
        Adds a new prompt to the database.

        Args:
            prompt (Prompt): The Prompt object to be added.
            prompt_id (int): The ID to assign to the prompt.
            domain_id (int): The domain ID.
            lang_id (int): The language ID.

        Returns:
            Optional[Prompts]: The Prompts object if found or created, otherwise None.
        """
        try:
            with self.Session() as session:
                # check of the prompt already exists in the database.
                existing_prompt = (
                    session.query(Prompts).filter_by(hash_value=prompt.digest).first()
                )
                if existing_prompt:
                    self.logger.debug(
                        f"Returning the existing prompt ID: {existing_prompt.prompt_id}"
                    )
                    raise ValueError(f"Prompt already exists")

                self.logger.debug(f"Adding new prompt: {prompt.user_prompt}")

                # create the orm object for the prompt to insert into the database table.
                new_prompt = Prompts(
                    prompt_id=prompt_id,
                    user_prompt=prompt.user_prompt,
                    system_prompt=prompt.system_prompt,
                    lang_id=lang_id,
                    domain_id=domain_id,
                    hash_value=prompt.digest,
                )

                # Add the new prompt to the session
                session.add(new_prompt)
                # Commit the session to save the new prompt
                session.commit()
                # Ensure prompt_id is populated
                session.refresh(new_prompt)

                self.logger.debug(f"Prompt added successfully: {new_prompt.prompt_id}")

                # Return the newly added prompt
                return new_prompt
        except IntegrityError as e:
            # Handle the case where the prompt already exists
            self.logger.error(f"Prompt already exists: {prompt} Error: {e}")
            return None

    def get_testcases_by_testplan(
        self,
        plan_name: str,
        n: int = 0,
        lang_names: Optional[str] = None,
        domain_name: Optional[str] = None,
    ) -> List[TestCase]:
        """
        Fetches test cases associated with a specific test plan.
        
        Args:
            plan_name (str): The name of the test plan to filter test cases.
            n (int): The number of test cases to fetch. If 0, fetches all matching test cases.
        
        Returns:
            List[TestCase]: A list of TestCase objects that match the criteria.
        """
        with self.Session() as session:
            # Construct the SQL query to fetch test plan associated with the specified test plan name
            existing_testplan = session.query(TestPlans).filter_by(plan_name=plan_name).first()
            if not existing_testplan:
                self.logger.error(f"Test plan '{plan_name}' does not exist.")
                return []

            self.logger.debug(f"Fetching test cases for test plan '{plan_name}' with limit {n} ..")
            # If the test plan exists, we will fetch the metrics associated with it
            metrics = existing_testplan.metrics
            if not metrics:
                self.logger.warning(f"No metrics found for test plan '{plan_name}'. Returning empty list.")
                return []
            
            self.logger.debug(f"Test plan '{plan_name}' has {len(metrics)} metrics associated with it.")
            
            # when we have more than one metric, we will fetch n/2 test cases for each metric.
            # If n is 0, we will fetch all test cases for each metric.
            n_metrics = len(metrics)
            if n_metrics > 1 and n > 0:
                n_per_metric = n // 2
            else:
                n_per_metric = n

            # Fetch the test cases associated with the specified test plan
            all_testcases = []
            # If there are multiple metrics, we will fetch test cases for each metric
            for metric in metrics:
                testcases = self.get_testcases_by_metric(metric.metric_name, n=n_per_metric, lang_names=lang_names, domain_name=domain_name)
                all_testcases.extend(testcases)

            self.logger.debug(f"Fetched {len(all_testcases)} test cases for test plan '{plan_name}'.")

            # If n is specified, we will return a random sample of n test cases
            if n > 0:
                # If n is specified, we will return a random sample of n test cases
                if len(all_testcases) < n:
                    self.logger.warning(f"Requested {n} test cases, but only {len(all_testcases)} are available. Returning all available test cases.")
                    return all_testcases
                else:
                    self.logger.debug(f"Returning a random sample of {n} test cases from {len(all_testcases)} available test cases.")
                    return random.sample(all_testcases, n)
               
            # If n is 0, we return all test cases, otherwise we return a random sample of n test cases
            return all_testcases
        
    def is_metric_in_testplan(self, metric_name: str, plan_name: str) -> bool:
        """
        Checks if a metric is associated with a specific test plan.
        
        Args:
            metric_name (str): The name of the metric to check.
            plan_name (str): The name of the test plan to check.

        Returns:
            bool: True if the metric is associated with the test plan, False otherwise.
        """
        with self.Session() as session:
            sql = select(Metrics).join(TestPlanMetricMapping).join(TestPlans).where(
                Metrics.metric_name == metric_name,
                TestPlans.plan_name == plan_name,
                TestPlanMetricMapping.metric_id == Metrics.metric_id,
                TestPlanMetricMapping.plan_id == TestPlans.plan_id
            )
            result = session.execute(sql).scalars().first()
            return result is not None

    def get_testcases_by_metric(self, metric_name:str, n:int = 0, lang_names:Optional[List[str]] = None, domain_name:Optional[str] = None) -> List[TestCase]:
        """
        Fetches test cases based on the metric name, language names, and domain name.
        
        Args:
            metric_name (str): The name of the metric to filter test cases.
            n (int): The number of test cases to fetch. If 0, fetches all matching test cases.
            lang_names (Optional[List[str]]): The names of the languages to filter test cases.
            domain_name (Optional[str]): The name of the domain to filter test cases.
        
        Returns:
            List[TestCase]: A list of TestCase objects that match the criteria.
        """
        domain_id = -1
        if domain_name:
            domain_id = self.get_domain_id(domain_name)

        with self.Session() as session:
            self.logger.debug(f"Fetching test cases for metric '{metric_name}' with limit {n} ..")
            sql = select(TestCases).join(Metrics, TestCases.metrics).where(Metrics.metric_name == metric_name)

            if lang_names:
                self.logger.debug(f"Filtering test cases by languages: {lang_names}")
                sql = sql.join(Prompts, TestCases.prompt).join(Languages, Prompts.lang_id == Languages.lang_id).where(Languages.lang_name.in_(lang_names))
            if domain_name:
                self.logger.debug(f"Filtering test cases by domain: {domain_name} (ID: {domain_id})")
                sql = sql.join(Prompts, TestCases.prompt).where((Prompts.domain_id == domain_id) | (Prompts.domain_id == 1))  # include prompts with domain_id = 1 (general) as well.
            if n > 0:
                # If n is specified, we order them randomly and limit the number of test cases returned
                sql = sql.order_by(func.random()).limit(n)
            
            result = session.execute(sql).scalars().all()
            testcases = [  TestCase(name=getattr(tc, 'testcase_name'),
                                    metric=metric_name,
                                    testcase_id=getattr(tc, 'testcase_id'),
                                    prompt=Prompt(prompt_id=getattr(tc.prompt, 'prompt_id'),
                                                user_prompt=str(tc.prompt.user_prompt),
                                                system_prompt=str(tc.prompt.system_prompt),
                                                lang_id=getattr(tc.prompt, 'lang_id')),
                                    response=Response(response_text=str(tc.response.response_text),
                                                    response_type=tc.response.response_type,
                                                    response_id=getattr(tc.response, 'response_id'),
                                                    prompt_id=tc.response.prompt_id,
                                                    lang_id=tc.response.lang_id,
                                                    digest=tc.response.hash_value) if tc.response else None,
                                    strategy=tc.strategy.strategy_name) for tc in result]
            
            self.logger.debug(f"Fetched {len(testcases)} test cases for metric '{metric_name}'.")
            return testcases

    def sample_prompts(self, 
                       lang_id: Optional[int] = None,
                       domain: Union[Optional[int], Optional[str]] = None,  # can be the domain id or name.
                       plan: Optional[Union[int, str]] = None,  # can be the plan id or name.
                       metric_id: Optional[int] = None ) -> List[Prompt]:
        """
        Fetches a sample of prompts from the database adhering to the specified filters.
        
        Returns:
            List[Prompt]: A list of Prompt objects.
        """
        with self.Session() as session:
            sql = select(Prompts)
            
            if lang_id is not None:
                sql = sql.where(Prompts.lang_id == lang_id)

            if domain is not None:
                if isinstance(domain, str):
                    sql = sql.join(Domains).where(Domains.domain_name == domain)
                else:
                    sql = sql.where(Prompts.domain_id == domain)
            if plan is not None:
                if isinstance(plan, str):
                    sql = sql.join(TestPlans).where(TestPlans.plan_name == plan)
                else:
                    sql = sql.where(TestPlans.plan_id == plan)
            if metric_id is not None:
                sql = sql.join(Metrics).where(Metrics.metric_id == metric_id)
            
            # Execute the query and return the results
            result = session.execute(sql).scalars().all()
            return [Prompt(prompt_id=prompt.prompt_id, 
                           user_prompt=str(prompt.user_prompt), 
                           system_prompt=str(prompt.system_prompt), 
                           lang_id=prompt.lang_id) for prompt in result]
        
    def add_metric_and_testcases(self, metric: Metric, testcases: List[TestCase]) -> bool:
        """
        Adds a new metric and its associated test cases to the database.
        
        Args:
            metric (Metric): The Metric object to be added.
            testcases (List[TestCase]): A list of TestCase objects associated with the metric.
        
        Returns:
            bool: True if the metric and test cases were added successfully, False if the metric already exists.
        """
        try:
            with self.Session() as session:
                # Create the Metrics object
                new_metric = self._get_or_create_metric(metric.metric_name,
                                                        metric.domain_id, 
                                                        metric.metric_description)
                
                new_testcases = []

                # Add each test case associated with the metric
                for testcase in testcases:
                    # Ensure the prompt is added first
                    prompt_id = self.add_or_get_prompt(testcase.prompt)
                    if prompt_id == -1:
                        self.logger.error(f"Prompt '{testcase.prompt.user_prompt}' already exists. Cannot add test case.")
                        return False
                    
                    judge_prompt_id = self.add_or_get_llm_judge_prompt(testcase.judge_prompt) if testcase.judge_prompt else None
                    if judge_prompt_id == -1:
                        self.logger.error(f"Judge prompt '{getattr(testcase.judge_prompt, 'prompt')}' already exists. Cannot add test case.")
                        return False
                    
                    # If a response is provided, create a Responses object
                    response_id = self.add_or_get_response(testcase.response, prompt_id) if testcase.response else None
                    # If the response already exists, use its ID
                    if response_id == -1:
                        self.logger.error(f"Response '{getattr(testcase.response, 'response_text')}' already exists. Cannot add test case.")
                        return False
                    
                    strategy_id = self.add_or_get_strategy_id(testcase.strategy) if isinstance(testcase.strategy, str) else testcase.strategy

                    # check if the test case is already present
                    existing_testcase = session.query(TestCases).filter_by(testcase_name=testcase.name).first()
                    if existing_testcase:
                        # we need to update the existing test case with the new metric
                        self.logger.debug(f"Test case '{testcase.name}' already exists. Checking for metrics ..")
                        # collect the metric names
                        metric_names = set([m.metric_name for m in existing_testcase.metrics])
                        if new_metric.metric_name not in metric_names:
                            # If the metric is not already associated with the test case, append it
                            self.logger.debug(f"Adding metric '{new_metric.metric_name}' to existing test case '{testcase.name}' ..")
                            existing_testcase.metrics.append(new_metric)
                        else:
                            self.logger.debug(f"Metric '{new_metric.metric_name}' already exists for test case '{testcase.name}'. Skipping ..")
                    else:
                        # If the test case does not exist, create a new one
                        self.logger.debug(f"Creating new test case '{testcase.name}' ..")
                        # Create the TestCases object with the prompt_id and response_id
                        # and the strategy and judge_prompt_id if provided.
                            
                        # Create the TestCases object
                        new_testcase = TestCases(testcase_name=testcase.name, 
                                                prompt_id=prompt_id, 
                                                response_id=response_id,
                                                strategy_id=strategy_id,
                                                judge_prompt_id=judge_prompt_id,
                                                metrics=[new_metric])  # Associate the metric with the test case
                        
                        # Add the new test case to the session
                        new_testcases.append(new_testcase)
                        #session.add(new_testcase)
                
                if len(new_testcases) == 0:
                    self.logger.debug(f"No new test cases to add for metric '{metric.metric_name}'.")
                    return True
                
                # Add the new metric to the session
                #session.add(new_metric)
                # Add all new test cases at once
                session.add_all(new_testcases)

                # Commit the session to save all changes
                session.commit()
                
                self.logger.debug(f"Metric '{metric.metric_name}' and its test cases added/updated successfully.")
                return True
        except IntegrityError as e:
            self.logger.error(f"Metric '{metric.metric_name}' already exists. Error: {e}")
            return False

    def add_testplan_and_metrics(self, plan: TestPlan, metrics: List[Metric]) -> bool:
        """
        Adds a new test plan and its associated metrics to the database.
        
        Args:
            plan (TestPlan): The TestPlan object to be added.
            metrics (List[Metric]): A list of Metric objects associated with the test plan.
        
        Returns:
            bool: True if the test plan and metrics were added successfully, False if the plan already exists.
        """
        try:
            with self.Session() as session:
                # Add each metric associated with the test plan
                #new_metrics = [Metrics(metric_name=metric.metric_name, domain_id = metric.domain_id, metric_description=metric.metric_description) for metric in metrics]
                new_metrics = [self._get_or_create_metric(metric.metric_name, metric.domain_id, metric.metric_description) for metric in metrics]
                    
                # Create the TestPlan object
                new_plan = TestPlans(plan_name=plan.plan_name, 
                                     plan_description=plan.plan_description,
                                     metrics=new_metrics)
                
                # Add the new test plan to the session
                session.add(new_plan)
                # Commit the session to save all changes
                session.commit()
                
                # Ensure plan_id is populated
                session.refresh(new_plan)  
                
                self.logger.debug(f"Test plan '{plan.plan_name}' and its metrics added successfully.")
                return True
        except IntegrityError as e:
            self.logger.error(f"Test plan '{plan.plan_name}' already exists. Error: {e}")
            return False        

    # Create or get Metrics objects from the database to ensure they are persistent
    def _get_or_create_metric(self, metric_name, domain_id: Optional[int] = None, metric_description: Optional[str] = None) -> Metrics:
        with self.Session() as session:
            self.logger.debug(f"Fetching or creating metric '{metric_name}' ..")
            # Check if the metric already exists in the database
            metric = session.query(Metrics).filter_by(metric_name=metric_name).first()
            if not metric:
                self.logger.debug(f"Metric '{metric_name}' does not exist. Creating a new one.")
                metric = Metrics(metric_name=metric_name, domain_id=domain_id, metric_description=metric_description)
                session.add(metric)
                session.commit()
            self.logger.debug(f"Returning metric ID: {metric.metric_id} for metric '{metric_name}'")
            return metric
        
    def add_or_get_llm_judge_prompt(self, judge_prompt: LLMJudgePrompt) -> int:
        """
        Adds a new LLM judge prompt to the database or fetches its ID if it already exists.
        
        Args:
            judge_prompt (LLMJudgePrompt): The LLMJudgePrompt object to be added.
        
        Returns:
            int: The ID of the newly added judge prompt, or -1 if it already exists.
        """
        try:
            with self.Session() as session:
                # Check if the judge prompt already exists in the database
                existing_judge_prompt = session.query(LLMJudgePrompts).filter_by(hash_value=judge_prompt.digest).first()
                if existing_judge_prompt:
                    self.logger.debug(f"Returning the existing judge prompt ID: {existing_judge_prompt.prompt_id}")
                    # Return the ID of the existing judge prompt
                    return getattr(existing_judge_prompt, "prompt_id")
                
                self.logger.debug(f"Adding new judge prompt: {judge_prompt.prompt}")

                # Create the LLMJudgePrompts object
                new_judge_prompt = LLMJudgePrompts(prompt=judge_prompt.prompt, 
                                                   lang_id=getattr(judge_prompt, "lang_id", Language.autodetect),  # Get the language ID from kwargs if provided
                                                   hash_value=judge_prompt.digest)
                
                # Add the new judge prompt to the session
                session.add(new_judge_prompt)
                # Commit the session to save the new judge prompt
                session.commit()
                # Ensure prompt_id is populated
                session.refresh(new_judge_prompt)  

                self.logger.debug(f"Judge prompt added successfully: {new_judge_prompt.prompt_id}")
                
                # Return the ID of the newly added judge prompt
                return getattr(new_judge_prompt, "prompt_id")
        except IntegrityError as e:
            # Handle the case where the judge prompt already exists
            self.logger.error(f"Judge prompt already exists: {judge_prompt}. Error: {e}")
            return -1
    

    def __add_or_get_llm_judge_prompt_custom_id(self, llm_prompt: str, llm_prompt_id: int, lang_id: int) -> Optional[LLMJudgePrompts]:
        """
        Adds a new LLM judge prompt to the database or fetches its ID if it already exists.

        Args:
            llm_prompt (str): The LLM prompt to be added.
            llm_prompt_id (int): The ID of the LLM prompt.
            lang_id (int): The ID of the language.

        Returns:
            int: The ID of the newly added judge prompt, or -1 if it already exists.
        """
        try:
            with self.Session() as session:
                existing_llm_prompt = session.query(LLMJudgePrompts).filter_by(prompt=llm_prompt).first()
                if existing_llm_prompt:
                    self.logger.debug(f"Returning the existing judge prompt: {existing_llm_prompt.prompt_id}")
                    raise ValueError(f"Judge prompt already exists")

                self.logger.debug(f"Adding new judge prompt: {llm_prompt}")

                # Create an LLMJudgePrompt instance from the string to get the digest
                judge_prompt_obj = LLMJudgePrompt(prompt=llm_prompt)

                # Create the LLMJudgePrompts object
                new_llm_prompt = LLMJudgePrompts(
                    prompt=llm_prompt, 
                    prompt_id=llm_prompt_id,
                    lang_id=lang_id,
                    hash_value=judge_prompt_obj.digest
                    )

                session.add(new_llm_prompt)
                session.commit()
                session.refresh(new_llm_prompt)
                self.logger.debug(f"Judge prompt added successfully: {new_llm_prompt.prompt}")
                return new_llm_prompt
        except IntegrityError as e:
            self.logger.error(f"Judge prompt already exists: {llm_prompt}. Error: {e}")
            return None

    def get_llm_prompt_by_id(self, prompt_id: int) -> Optional[LLMJudgePrompt]:
        """
        Fetches an LLM prompt by its ID.

        Args:
            prompt_id (int): The ID of the LLM prompt to fetch.

        Returns:
            Optional[LLMPrompt]: The LLM prompt object if found, otherwise None.
        """
        with self.Session() as session:
            sql = select(LLMJudgePrompts).where(LLMJudgePrompts.prompt_id == prompt_id)
            result = session.execute(sql).scalar_one_or_none()
            if result is None:
                self.logger.error(f"LLM prompt with ID '{prompt_id}' does not exit")
                return None
            # Return an LLM prompt object with the fetched data
            return LLMJudgePrompt(
                prompt_id=getattr(result, "prompt_id"),
                prompt=str(result.prompt),
                lang_id=getattr(result, "lang_id"),
            )


    def get_target_by_id(self, target_id: int) -> Optional[Target]:
        """
        Fetches a target by its ID.
        
        Args:
            target_id (int): The ID of the target to fetch.
        
        Returns:
            Optional[Target]: The Target object if found, otherwise None.
        """
        with self.Session() as session:
            sql = select(Targets).where(Targets.target_id == target_id)
            result = session.execute(sql).scalar_one_or_none()
            if result is None:
                self.logger.error(f"Target with ID '{target_id}' does not exist.")
                return None
            # Return a Target object with the fetched data
            return Target(target_id=getattr(result, 'target_id'),
                          target_name=str(result.target_name),
                          target_type=str(result.target_type),
                          target_description=str(result.target_description),
                          target_url=str(result.target_url),
                          target_domain=result.domain.domain_name,
                          target_languages=[lang.lang_name for lang in result.langs])
        
    def get_target_by_name(self, target_name: str) -> Optional[Target]:
        """
        Fetches a target by its name.
        
        Args:
            target_name (str): The name of the target to fetch.
        
        Returns:
            Optional[Target]: The Target object if found, otherwise None.
        """
        with self.Session() as session:
            sql = select(Targets).where(Targets.target_name == target_name)
            result = session.execute(sql).scalar_one_or_none()
            if result is None:
                self.logger.error(f"Target with name '{target_name}' does not exist.")
                return None
            # Return a Target object with the fetched data
            return Target(target_id=getattr(result, 'target_id'),
                          target_name=str(result.target_name),
                          target_type=str(result.target_type),
                          target_description=str(result.target_description),
                          target_url=str(result.target_url),
                          target_domain=result.domain.domain_name,
                          target_languages=[lang.lang_name for lang in result.langs])
        
    def add_or_get_target(self, target: Target) -> int:
        """
        Adds a new target to the database or fetches its ID if it already exists.
        
        Args:
            target (Target): The Target object to be added.
        
        Returns:
            int: The ID of the newly added target, or -1 if it already exists.
        """
        try:
            with self.Session() as session:
                # Check if the target already exists in the database
                existing_target = session.query(Targets).filter_by(target_name=target.target_name).first()
                if existing_target:
                    self.logger.debug(f"Returning the existing target ID: {existing_target.target_id}")
                    # Return the ID of the existing target
                    return getattr(existing_target, "target_id")
                
                self.logger.debug(f"Adding new target: {target.target_name}")

                # get the domain ID if provided, otherwise use None
                domain_id = self.add_or_get_domain_id(target.target_domain) if target.target_domain else None
                # get the language objects for the target languages, if provided
                langs = [self.__add_or_get_language(lang) for lang in target.target_languages] if target.target_languages else None

                # Create the Targets object
                new_target = Targets(target_name=target.target_name,
                                     target_type=target.target_type,
                                     target_description=target.target_description,
                                     target_url=target.target_url,
                                     domain_id=domain_id,  # Use the domain ID if provided
                                     langs = langs)
                
                # Add the new target to the session
                session.add(new_target)
                # Commit the session to save the new target
                session.commit()
                # Ensure target_id is populated
                session.refresh(new_target)  

                self.logger.debug(f"Target added successfully: {new_target.target_id}")
                
                # Return the ID of the newly added target
                return getattr(new_target, "target_id")
        except IntegrityError as e:
            # Handle the case where the target already exists
            self.logger.error(f"Target already exists: {target}. Error: {e}")
            return -1
        
    def __add_or_get_target_custom_id(self, target: Target, target_id:int, domain_id:int) -> Optional[Targets]:
        
        """
        Adds a target with a custom ID or returns the existing target.

        Args:
            target (Target): The target object to add.
            target_id (int): The custom ID to use for the target.

        Returns:
            Optional[Targets]: The target object if successful, otherwise None.
        """
        try:
            with self.Session() as session:
                
                #check if the target already exists in the database
                existing_target = session.query(Targets)\
                    .options(joinedload(Targets.domain), joinedload(Targets.langs))\
                    .filter(
                        (Targets.target_name == target.target_name) |
                        (Targets.target_url == target.target_url)
                    )\
                    .first()
                
                # URL uniqueness validation
                if target.target_url:
                    existing_url = session.query(Targets).filter(Targets.target_url == target.target_url).first()
                    if existing_url:
                        raise ValueError(f"Target with URL '{target.target_url}' already exists.")

                if target.target_name:
                    existing_name = session.query(Targets).filter(Targets.target_name == target.target_name).first()
                    if existing_name:
                        raise ValueError(f"Target with name '{target.target_name}' already exists.")

                if existing_target:
                    self.logger.debug(
                        f"Returning the existing target ID: {existing_target.target_id}"
                    )
                    return existing_target
                
                self.logger.debug(f"Adding new Target with custom target_id {target_id}: {target.target_name}")
                
                # get the domain ID if provided, otherwise use None
                # domain_id = (
                #     self.add_or_get_domain_id(target.target_domain)
                #     if target.target_domain
                #     else None
                # )
                
                # Get the language list from either target_languages or lang_list attribute
                # if hasattr(target, 'target_languages') and target.target_languages is not None:
                #     lang_list = target.target_languages
                # elif hasattr(target, 'lang_list') and target.lang_list is not None:
                #     lang_list = target.lang_list
                # else:
                #     lang_list = []
                
                # Get language objects for the target languages
                langs = [self.__add_or_get_language(lang) for lang in target.target_languages] if target.target_languages else []
                
                new_target = Targets(
                    target_id = target_id,
                    target_name = target.target_name,
                    target_type = target.target_type,
                    target_description = target.target_description,
                    target_url = target.target_url,
                    domain_id = domain_id,
                    langs = langs
                )
                
                
                session.add(new_target)
                session.commit()
                session.refresh(new_target)
                
                # Ensure relationships are loaded
                if new_target.domain:
                    _ = new_target.domain.domain_name
                if new_target.langs:
                    _ = [lang.lang_name for lang in new_target.langs]
                
                self.logger.debug(f"Target added successfully: {new_target.target_name} (ID: {new_target.target_id})")
                
                return new_target
        except IntegrityError as e:
            session.rollback()
            self.logger.error(f"Error adding target: {e}")
            raise
        except Exception as e:
            session.rollback()
            self.logger.error(f"Unexpected error adding target: {e}")
            raise
        finally:
            session.close()

    def get_target_id(self, target_name: str) -> Optional[int]:
        """
        Fetches the ID of a target by its name.
        
        Args:
            target_name (str): The name of the target to fetch.
        
        Returns:
            Optional[int]: The ID of the target if found, otherwise None.
        """
        target = self.__get_target(target_name)
        if target:
            return getattr(target, "target_id")
        return None
        
    def __get_target(self, target_name:str) -> Optional[Targets]:
        """
        Fetches a target by its name.
        
        Args:
            target_name (str): The name of the target to fetch.
        
        Returns:
            Optional[Targets]: The Targets object if found, otherwise None.
        """
        with self.Session() as session:
            sql = select(Targets).where(Targets.target_name == target_name)
            result = session.execute(sql).scalar_one_or_none()
            if result is None:
                self.logger.error(f"Target with name '{target_name}' does not exist.")
                return None
            # Return a Targets object with the fetched data
            return Targets(
                target_id=getattr(result, "target_id"),
                target_name=str(result.target_name),
                target_type=str(result.target_type),
                target_description=str(result.target_description),
                target_url=str(result.target_url),
                domain_id=getattr(result, "domain_id"),
                langs=result.langs,
            )
            
    def __add_or_get_test_case_custom_id(self, testcase: TestCase, testcase_id: int = None) -> Optional[TestCases]:
        """
        Adds a new test case with a custom ID or returns an existing one.
        
        Args:
            testcase: The TestCase object to add
            testcase_id: Optional custom ID for the test case
            
        Returns:
            The created or existing TestCases ORM object, or None if there was an error
        """
        with self.Session() as session:
            try:
                # Check if test case with this name already exists
                existing_testcase = (
                    session.query(TestCases)
                    .filter(TestCases.testcase_name == testcase.name)
                    .first()
                )
                
                if existing_testcase:
                    self.logger.warning(f"Test case '{testcase.name}' already exists")
                    return existing_testcase
                    
                # Get or create prompt
                prompt_id = self.add_or_get_prompt(testcase.prompt)
                if prompt_id == -1:
                    self.logger.error("Failed to get or create prompt")
                    return None
                    
                # Get or create response if provided
                response_id = None
                if testcase.response:
                    response_id = self.add_or_get_response(testcase.response, prompt_id)
                    if response_id == -1:
                        self.logger.error("Failed to get or create response")
                        return None
                        
                # Get or create judge prompt if provided
                judge_prompt_id = None
                if testcase.judge_prompt:
                    judge_prompt_id = self.add_or_get_llm_judge_prompt(testcase.judge_prompt)
                    if judge_prompt_id == -1:
                        self.logger.error("Failed to get or create judge prompt")
                        return None
                        
                # Get strategy ID
                strategy_id = self.add_or_get_strategy_id(testcase.strategy)
                if strategy_id == -1:
                    self.logger.error(f"Strategy '{testcase.strategy}' not found")
                    return None
                    
                # Create new test case
                new_testcase = TestCases(
                    testcase_id=testcase_id,  # Will be None for auto-increment
                    testcase_name=testcase.name,
                    prompt_id=prompt_id,
                    response_id=response_id,
                    judge_prompt_id=judge_prompt_id,
                    strategy_id=strategy_id
                )
                
                session.add(new_testcase)
                session.commit()
                session.refresh(new_testcase)
                
                # Add default metric if none exists
                if not new_testcase.metrics:
                    default_metric = session.query(Metrics).first()
                    if default_metric:
                        new_testcase.metrics.append(default_metric)
                        session.commit()
                        session.refresh(new_testcase)
                
                self.logger.info(f"Test case '{testcase.name}' created with ID: {new_testcase.testcase_id}")
                return new_testcase
                
            except Exception as e:
                session.rollback()
                self.logger.error(f"Error creating test case: {str(e)}")
                return None
    

    def __status_compare(self, status1: str, status2: str) -> int:
        """
        Compares two statuses to determine if they are the same.
        
        Args:
            status1 (str): The first status to compare.
            status2 (str): The second status to compare.
        
        Returns:
            int: 0 if the statuses are the same (case-insensitive), 1 if status1 is greater, -1 if status2 is greater. -2 if either status is invalid.
        """
        lookup = {"new": 0, "running": 1, "completed": 3, "failed": 2}
        s1 = lookup.get(status1.lower(), -1)
        s2 = lookup.get(status2.lower(), -1)
        if s1 == -1 or s2 == -1:
            self.logger.error(f"Invalid status comparison: {status1} vs {status2}")
            return -2
        if s1 == s2:
            return 0
        return 1 if s1 > s2 else -1
    
    def get_run_by_name(self, run_name: str) -> Optional[Run]:
        """
        Fetches a test run by its name.
        
        Args:
            run_name (str): The name of the test run to fetch.
        
        Returns:
            Optional[Run]: The Run object if found, otherwise None.
        """
        with self.Session() as session:
            sql = select(TestRuns).where(TestRuns.run_name == run_name)
            result = session.execute(sql).scalar_one_or_none()
            if result is None:
                self.logger.error(f"TestRun with name '{run_name}' does not exist.")
                return None
            return Run(target=result.target.target_name,
                       run_name=str(result.run_name),
                       target_id=getattr(result, 'target_id'),
                       start_ts=result.start_ts.isoformat(),
                       end_ts=result.end_ts.isoformat() if getattr(result, "end_ts") else None,
                       status=str(result.status),
                       run_id=getattr(result, 'run_id'))
    
    def get_run_by_id(self, run_id: int) -> Optional[Run]:
        """
        Fetches a test run by its ID.
        
        Args:
            run_id (int): The ID of the test run to fetch.
        
        Returns:
            Optional[Run]: The Run object if found, otherwise None.
        """
        with self.Session() as session:
            sql = select(TestRuns).where(TestRuns.run_id == run_id)
            result = session.execute(sql).scalar_one_or_none()
            if result is None:
                self.logger.error(f"TestRun with ID '{run_id}' does not exist.")
                return None
            return Run(target=result.target.target_name,
                       run_name=str(result.run_name),
                       target_id=getattr(result, 'target_id'),
                       start_ts=result.start_ts.isoformat(),
                       end_ts=result.end_ts.isoformat(),
                       status=str(result.status),
                       run_id=getattr(result, 'run_id'))
    
    def _ensure_datetime(self, value):
        if value is None:
            return None
        if isinstance(value, datetime):
            return value
        try:
            return datetime.fromisoformat(value)
        except Exception:
            return None

    def add_or_update_testrun(self, run: Run, override:bool = False) -> int:
        """
        Adds a new test run to the database or fetches its ID if it already exists.
        
        Args:
            run (Run): The Run object to be added.
        
        Returns:
            int: The ID of the newly added run, or -1 if it already exists.
        """
        try:
            with self.Session() as session:
                # Check if the run already exists in the database
                existing_run = session.query(TestRuns).filter_by(run_name=run.run_name).first()
                if existing_run:
                    if run.status == "NEW":
                        self.logger.error(f"TestRun (name={run.run_name}) already exists.")
                        #return -1  # Return -1 if the run already exists and is not being updated
                        # Return the ID of the existing run if the status is the same
                        return getattr(existing_run, "run_id")
                    
                    if not override and self.__status_compare(run.status, getattr(existing_run, "status")) <= 0:
                        self.logger.debug(f"Run '{run.run_name}:{existing_run.status}' already exists, can't update with '{run.status}'. Returning existing run ID: {existing_run.run_id}")
                        # Return the ID of the existing run if the status is the same
                        return getattr(existing_run, "run_id")
                    
                    # update the existing run with new details
                    self.logger.debug(f"Run '{run.run_name}' already exists. Updating existing run details (Status: {existing_run.status} -> {run.status}, TS: {existing_run.end_ts} -> {run.end_ts}) ..")
                    setattr(existing_run, "end_ts", self._ensure_datetime(run.end_ts))  # Update the end timestamp
                    setattr(existing_run, "status", run.status)  # Update the status

                    # Commit the session to save the updated run
                    session.commit()
                    # Ensure run_id is populated
                    session.refresh(existing_run)   
                    # Log the existing run ID
                    self.logger.debug(f"Returning the ID of the updated run ID: {existing_run.run_id}")
                    # Return the ID of the existing run
                    return getattr(existing_run, "run_id")
                
                self.logger.debug(f"Adding a run: {run.run_name} with status: {run.status}")

                # Fetch the target object from the database
                # If the target does not exist, it will return None
                #target_obj = self.__get_target(run.target)
                target_id = self.get_target_id(run.target) if run.target else None

                # Create the Runs object
                new_run = TestRuns(run_name=run.run_name,
                                   target_id = target_id,  # Use the target ID if the target exists
                                   start_ts=self._ensure_datetime(run.start_ts),            # made changes for supporting both mariadb and sqlite
                                   end_ts=self._ensure_datetime(run.end_ts),
                                   status=run.status)
                
                # Add the new run to the session
                session.add(new_run)
                # Commit the session to save the new run
                session.commit()
                # Ensure run_id is populated
                session.refresh(new_run)  

                self.logger.debug(f"Run added successfully: {new_run.run_id}")
                
                # Return the ID of the newly added run
                return getattr(new_run, "run_id")
        except IntegrityError as e:
            # Handle the case where the run already exists
            self.logger.error(f"Run already exists: {run}. Error: {e}")
            return -1
        
    def get_run_id(self, run_name: str) -> Optional[int]:
        """
        Fetches the ID of a test run by its name.
        
        Args:
            run_name (str): The name of the test run to fetch.
        
        Returns:
            Optional[int]: The ID of the test run if found, otherwise None.
        """
        with self.Session() as session:
            sql = select(TestRuns).where(TestRuns.run_name == run_name)
            result = session.execute(sql).scalar_one_or_none()
            if result is None:
                self.logger.error(f"TestRun with name '{run_name}' does not exist.")
                return None
            return getattr(result, 'run_id')
        
    def get_testcase_strategy_name(self, testcase_name: str) -> Optional[str]:
        """
        Fetches the strategy name of a test case by its name.

        Args:
            testcase_name (str): The name of the test case to fetch.

        Returns:
            Optional[str]: The strategy name of the test case if found, otherwise None.
        """
        with self.Session() as session:
            sql = select(Strategies.strategy_name) \
                    .join(TestCases, Strategies.strategy_id == TestCases.strategy_id) \
                    .where(TestCases.testcase_name == testcase_name)
            result = session.execute(sql).scalar_one_or_none()
            if result is None:
                self.logger.error(f"TestCase with name '{testcase_name}' does not exist.")
                return None
            return result


    def create_domain_v2(self, payload: dict) -> int:
        with self.Session() as session:
            if (
                session.query(Domains)
                .filter_by(domain_name=payload["domain_name"])
                .first()
            ):
                raise IntegrityError(
                    "Domain name already exists", params=None, orig=None
                )
            new_domain = Domains(domain_name=payload["domain_name"])
            session.add(new_domain)
            session.commit()
            session.refresh(new_domain)
            return new_domain.domain_id

    def update_domain_v2(self, domain_id: int, updates: dict) -> Optional[dict]:
        """Updates a domain similar to the v1 logic but returns a v2-style dict."""
        with self.Session() as session:
            domain = (
                session.query(Domains).filter(Domains.domain_id == domain_id).first()
            )
            if not domain:
                return None
            if "domain_name" in updates:
                # Check if name already exists (excluding current domain)
                existing = (
                    session.query(Domains)
                    .filter(
                        Domains.domain_name == updates["domain_name"],
                        Domains.domain_id != domain_id
                    )
                    .first()
                )
                if existing:
                    raise ValueError("Domain name already exists")
                domain.domain_name = updates["domain_name"]
            session.commit()
            session.refresh(domain)
            
            # Return the updated domain as a dict (domain_name is a column, not a relationship)
            return {
                "domain_id": domain.domain_id,
                "domain_name": domain.domain_name
            }

    def delete_domain_record(self, domain_id: int) -> bool:
        with self.Session() as session:
            domain = (
                session.query(Domains).filter(Domains.domain_id == domain_id).first()
            )
            if not domain:
                return False
            
            # Check if domain is used in Prompts that are referenced by TestCases
            prompts_with_domain = session.query(Prompts).filter(Prompts.domain_id == domain_id).all()
            if prompts_with_domain:
                # Check if any of these prompts are used in TestCases
                prompt_ids = [p.prompt_id for p in prompts_with_domain]
                testcases_using_prompts = session.query(TestCases).filter(TestCases.prompt_id.in_(prompt_ids)).first()
                if testcases_using_prompts:
                    raise ValueError("This domain cannot be deleted because it is used in the TestCase table.")
            
            session.delete(domain)
            session.commit()
            return True


    def create_language_v2(self, payload: str, next_id: int) -> Optional[Languages]:
        with self.Session() as session:
            if (
                session.query(Languages)
                .filter_by(lang_name=payload)
                .first()
            ):
                raise IntegrityError(
                    "Language name already exists", params=None, orig=None
                )
            new_language = Languages(lang_id=next_id, lang_name=payload)
            session.add(new_language)
            session.commit()
            session.refresh(new_language)
            return new_language.lang_id

    def update_language_v2(self, lang_id: int, updates: dict) -> Optional[dict]:
        """Updates a language similar to the v1 logic but returns a v2-style dict."""
        with self.Session() as session:
            language = (
                session.query(Languages).filter(Languages.lang_id == lang_id).first()
            )
            if not language:
                return None
            if "lang_name" in updates:
                # Check if name already exists (excluding current language)
                existing = (
                    session.query(Languages)
                    .filter(
                        Languages.lang_name == updates["lang_name"],
                        Languages.lang_id != lang_id
                    )
                    .first()
                )
                if existing:
                    raise ValueError("Language name already exists")
                language.lang_name = updates["lang_name"]
            session.commit()
            session.refresh(language)
            
            # No need for joinedload on a column property
            language_updated = (
                session.query(Languages)
                    .filter(Languages.lang_id == lang_id)
                    .first()
            )
            
            
            return language_updated

    def delete_language_record(self, lang_id: int) -> bool:
        with self.Session() as session:
            language = (
                session.query(Languages).filter(Languages.lang_id == lang_id).first()
            )
            if not language:
                return False
            session.delete(language)
            session.commit()
            return True

    def create_llm_prompt_v2(self, payload: dict) -> int:
        with self.Session() as session:
            lang_id = self.add_or_get_language_id(payload["language"])
            if lang_id == -1:
                raise ValueError("Failed to create or get language")

            new_llm_prompt = LLMJudgePrompts(
                prompt=payload["prompt"],
                lang_id=lang_id,
                hash_value=LLMJudgePrompt(
                    prompt=payload["prompt"], lang_id=lang_id
                ).digest,
            )
            session.add(new_llm_prompt)
            session.commit()
            session.refresh(new_llm_prompt)
            return new_llm_prompt.prompt_id

    def update_llm_prompt_v2(self, llm_prompt_id: int, updates: dict) -> Optional[dict]:
        """Updates an LLM prompt similar to the v1 logic but returns a v2-style dict."""
        with self.Session() as session:
            # llm_prompt = (
            #     session.query(LLMJudgePrompts)
            #     .options(joinedload(LLMJudgePrompts.lang))
            #     .filter(LLMJudgePrompts.prompt_id == llm_prompt_id)
            #     .first()
            # )
            llm_prompt = (
                session.query(LLMJudgePrompts)
                .filter(LLMJudgePrompts.prompt_id == llm_prompt_id)
                .first()
            )
            if not llm_prompt:
                raise ValueError(f"LLM prompt with ID {llm_prompt_id} not found")
                
            updated = False

            if "prompt" in updates and updates["prompt"]:
                existing_prompt = (
                    session.query(LLMJudgePrompts)
                    .filter(
                        LLMJudgePrompts.prompt == updates["prompt"],
                        LLMJudgePrompts.prompt_id != llm_prompt_id
                    )
                    .first()
                )
                if existing_prompt:
                    raise ValueError("Prompt already exists")

                # if updates["prompt"] is None:
                #     raise {
                #         "title": "ValueError",
                #         "detail": "Prompt cannot be empty",
                #     }
                    

                llm_prompt.prompt = updates["prompt"]

                updated = True

                # llm_prompt.prompt = updates["prompt"]
                # llm_prompt.hash_value = LLMJudgePrompt(
                #     prompt=updates["prompt"], lang_id=llm_prompt.lang_id
                # ).digest
            if "language" in updates and updates["language"]:
                language = (
                    session.query(Languages)
                    .filter(Languages.lang_name == updates["language"])
                    .first()
                )
                if not language:
                    raise HTTPException(status_code=404, detail="Language not found")
                llm_prompt.lang_id = language.lang_id

                updated = True

                # lang_id = self.add_or_get_language_id(updates["language"])
                # if lang_id is None:
                #     raise ValueError(f"Language '{updates['language']}' not found")
                # llm_prompt.lang_id = lang_id
                # # Recompute hash if language changed
                # if "prompt" not in updates:
                #     llm_prompt.hash_value = LLMJudgePrompt(
                #         prompt=llm_prompt.prompt, lang_id=lang_id
                #     ).digest

            if updated:
                session.commit()
            else:
                session.refresh(llm_prompt)
            # session.refresh(llm_prompt)
            
            # Reload with relationships for serialization
            llm_prompt = (
                session.query(LLMJudgePrompts)
                .options(joinedload(LLMJudgePrompts.lang))
                .filter(LLMJudgePrompts.prompt_id == llm_prompt_id)
                .first()
            )
            return llm_prompt

    def delete_llm_prompt_record(self, llm_prompt_id: int) -> bool:
        with self.Session() as session:
            llm_prompt = (
                session.query(LLMJudgePrompts)
                .filter(LLMJudgePrompts.prompt_id == llm_prompt_id)
                .first()
            )
            if not llm_prompt:
                return False
            session.delete(llm_prompt)
            session.commit()
            return True

    def create_prompt_v2(self, payload: dict) -> int:
        with self.Session() as session:
            lang_id = self.add_or_get_language_id(payload["language"])
            domain_id = self.add_or_get_domain_id(payload["domain"])
            if lang_id == -1 or domain_id == -1:
                raise ValueError("Failed to create or get language or domain")

            new_prompt = Prompts(
                user_prompt=payload["user_prompt"],
                system_prompt=payload.get("system_prompt"),
                lang_id=lang_id,
                domain_id=domain_id,
                hash_value=Prompt(
                    user_prompt=payload["user_prompt"],
                    system_prompt=payload.get("system_prompt"),
                    lang_id=lang_id,
                    domain_id=domain_id,
                ).digest,
            )
            session.add(new_prompt)
            session.commit()
            session.refresh(new_prompt)
            return new_prompt.prompt_id

    def update_prompt_v2(self, prompt_id: int, updates: dict) -> Optional[dict]:
        """Updates a prompt similar to the v1 logic but returns a v2-style dict."""
        with self.Session() as session:
            prompt = (
                session.query(Prompts)
                .options(joinedload(Prompts.lang), joinedload(Prompts.domain))
                .filter(Prompts.prompt_id == prompt_id)
                .first()
            )
            if not prompt:
                raise ValueError(f"Prompt with ID {prompt_id} not found")
            
            previous_language = getattr(prompt.lang, "lang_name", None) if prompt.lang else None

            updated = False
            
            if "user_prompt" in updates or "system_prompt" in updates:
                new_user_prompt = updates.get("user_prompt", prompt.user_prompt)
                new_system_prompt = updates.get("system_prompt", prompt.system_prompt)
                
                prompt.user_prompt = new_user_prompt
                prompt.system_prompt = new_system_prompt
                
                # update hash_value
                prompt_str = f"System: '{prompt.system_prompt or ''}'\tUser: '{prompt.user_prompt}'"
                
                hashing = hashlib.sha1()
                hashing.update(prompt_str.encode("utf-8"))
                prompt.hash_value = hashing.hexdigest()
                updated = True

            if "language" in updates and updates["language"]:
                language = (
                    session.query(Languages)
                    .filter(Languages.lang_name == updates["language"])
                    .first()
                )
                if not language:
                    raise ValueError(f"Language '{updates['language']}' not found")
                prompt.lang_id = language.lang_id
                updated = True

            if "domain" in updates and updates["domain"]:
                domain = (
                    session.query(Domains)
                    .filter(Domains.domain_name == updates["domain"])
                    .first()
                )
                if not domain:
                    raise ValueError(f"Domain '{updates['domain']}' not found")
                prompt.domain_id = domain.domain_id
                updated = True
                
                
                # domain_id = self.add_or_get_domain_id(updates["domain"])
                # if domain_id is None:
                #     raise ValueError(f"Domain '{updates['domain']}' not found")
                # prompt.domain_id = domain_id

            # Update hash value when prompt content changes
            # prompt.hash_value = Prompt(
            #     user_prompt=prompt.user_prompt,
            #     system_prompt=prompt.system_prompt,
            #     lang_id=prompt.lang_id,
            #     domain_id=prompt.domain_id,
            # ).digest
            # session.commit()
            # session.refresh(prompt)


            if updated:
                session.commit()
            else:
                session.refresh(prompt)
            
            # Reload with relationships for serialization
            prompt = (
                session.query(Prompts)
                .options(joinedload(Prompts.lang), joinedload(Prompts.domain))
                .filter(Prompts.prompt_id == prompt_id)
                .first()
            )
            return prompt

    def delete_prompt_record(self, prompt_id: int) -> bool:
        with self.Session() as session:
            prompt = session.query(Prompts).filter(Prompts.prompt_id == prompt_id).first()
            if not prompt:
                return False
            
            # First, delete any TestCases that directly reference this prompt_id
            # since prompt_id is NOT NULL in TestCases, we must delete them
            # before deleting the prompt to avoid violating the NOT NULL constraint.
            testcases_with_prompt = (
                session.query(TestCases)
                .filter(TestCases.prompt_id == prompt_id)
                .all()
            )
            for tc in testcases_with_prompt:
                session.delete(tc)
            
            # Then detach any TestCases that reference Responses for this prompt
            # by nulling out their response_id, so that we can safely delete
            # the corresponding Responses rows without violating FK constraints.
            testcases_with_responses = (
                session.query(TestCases)
                .join(Responses, TestCases.response_id == Responses.response_id)
                .filter(Responses.prompt_id == prompt_id)
                .all()
            )
            for tc in testcases_with_responses:
                tc.response_id = None

            # Delete any Responses that reference this prompt_id to avoid
            # violating the NOT NULL constraint on Responses.prompt_id.
            session.query(Responses).filter(Responses.prompt_id == prompt_id).delete(
                synchronize_session=False
            )
            session.delete(prompt)
            session.commit()
            return True


    def create_response_v2(self, payload: dict) -> int:
        with self.Session() as session:
            lang_id = self.add_or_get_language_id(payload["language"])
            if lang_id == -1:
                raise ValueError("Failed to create or get language")

            new_response = Responses(
                response_text=payload["response_text"],
                response_type=payload["response_type"],
                lang_id=lang_id,
                prompt_id=payload["prompt_id"],
                hash_value=Response(
                    response_text=payload["response_text"],
                    response_type=payload["response_type"],
                    lang_id=lang_id,
                ).digest,
            )
            session.add(new_response)
            session.commit()
            session.refresh(new_response)
            return new_response.response_id

    def update_response_v2(self, response_id: int, updates: dict) -> Optional[dict]:
        """
        Updates a response similar to the v1 logic but returns a v2-style dict.
        Handles response_text, response_type, language, and prompt updates.
        """
        with self.Session() as session:
            try:
                # Load response with relationships
                response = (
                    session.query(Responses)
                    .options(joinedload(Responses.prompt), joinedload(Responses.lang))
                    .filter(Responses.response_id == response_id)
                    .with_for_update()
                    .first()
                )
                if not response:
                    return None

                updated = False

                # Update response text if provided
                if "response_text" in updates and updates["response_text"] is not None:
                    new_text = updates["response_text"].strip()
                    if new_text and response.response_text != new_text:
                        # Compute hash for response
                        response_str = f"Response Text: '{new_text}'\tResponse Type: '{response.response_type}'"
                        hashing = hashlib.sha1()
                        hashing.update(response_str.encode('utf-8'))
                        new_hash = hashing.hexdigest()

                        # Check if a response with this hash already exists (excluding current response)
                        existing_response = (
                            session.query(Responses)
                            .filter(
                                Responses.hash_value == new_hash,
                                Responses.response_id != response_id
                            )
                            .first()
                        )

                        if existing_response:
                            raise ValueError("A response with this text already exists")
                        
                        response.response_text = new_text
                        response.hash_value = new_hash

                        updated = True

                # Update response type if provided
                if "response_type" in updates and updates["response_type"] is not None:
                    if response.response_type != updates["response_type"]:
                        response.response_type = updates["response_type"]
                        # Recompute hash with new response type
                        response_str = (
                            f"Response Text: '{response.response_text}'\t"
                            f"Response Type: '{response.response_type}'"
                        )
                        hashing = hashlib.sha1()
                        hashing.update(response_str.encode('utf-8'))
                        response.hash_value = hashing.hexdigest()

                        updated = True

                # Update language if provided
                if "language" in updates and updates["language"] is not None:

                    lang = (
                        session.query(Languages)
                        .filter(Languages.lang_name == updates["language"])
                        .first()
                    )
                    if lang is None:
                        raise ValueError(f"Language '{updates['language']}' not found")

                    if response.lang_id != lang.lang_id:
                        response.lang_id = lang.lang_id

                        updated = True

                    # lang_id = self.add_or_get_language_id(updates["language"])
                    # if lang_id is None:
                    #     raise ValueError(f"Language '{updates['language']}' not found")
                    # if response.lang_id != lang_id:
                    #     response.lang_id = lang_id


                if ( "user_prompt" in updates or "system_prompt" in updates ):

                    user_prompt_input = updates["user_prompt"] 
                    system_prompt_input = updates["system_prompt"] 

                    user_prompt_changed = (
                        user_prompt_input is not None 
                        and (
                            not response.prompt
                            or user_prompt_input != (response.prompt.user_prompt or "")
                        )
                    )

                    system_prompt_changed = (
                        system_prompt_input is not None
                        and (
                            not response.prompt
                            or system_prompt_input != (response.prompt.system_prompt or "")
                        )
                    )

                    if user_prompt_changed or system_prompt_changed:
                        new_user_prompt = (
                            user_prompt_input
                            if user_prompt_input is not None
                            else (response.prompt.user_prompt if response.prompt else "")
                        )
                        new_system_prompt = (
                            system_prompt_input
                            if system_prompt_input is not None
                            else (response.prompt.system_prompt if response.prompt else "")
                        )

                        system_prompt_value = ( new_system_prompt.strip() if new_system_prompt else "")

                        prompt_str = (
                            f"System:'{system_prompt_value}'/t"
                            f"User:'{new_user_prompt}'"
                        )

                        hashing = hashlib.sha1()
                        hashing.update(prompt_str.encode('utf-8'))
                        new_hash = hashing.hexdigest()

                        # Check if a prompt with this hash already exists (excluding current prompt)
                        existing_prompt = (
                            session.query(Prompts)
                            .filter(Prompts.hash_value == new_hash)
                            .first()
                        )

                        if existing_prompt:
                            # Point response to existing prompt
                            response.prompt_id = existing_prompt.prompt_id
                        else:
                            if response.prompt:
                                # Update existing prompt
                                if user_prompt_changed:
                                    response.prompt.user_prompt = new_user_prompt
                                if system_prompt_changed:
                                        response.prompt.system_prompt = (
                                            system_prompt_value
                                            if system_prompt_value
                                            else None
                                        )
                                response.prompt.hash_value = new_hash
                            else:
                                # Create new prompt with default lang/domain
                                default_lang = session.query(Languages).first()
                                if not default_lang:
                                    raise ValueError(
                                        "No language found in database."
                                        "Please add a language first."
                                    )

                                default_domain = session.query(Domains).first()
                                if not default_domain:
                                    raise ValueError(
                                        "No domains found in database."
                                        "Please add a domain first."
                                    )

                                new_prompt = Prompts(
                                    user_prompt=new_user_prompt,
                                    system_prompt=(
                                        system_prompt_value if system_prompt_value else None
                                    ),
                                    lang_id=default_lang.lang_id,
                                    domain_id=default_domain.domain_id,
                                    hash_value=new_hash,
                                )

                                session.add(new_prompt)
                                session.flush()
                                response.prompt_id = new_prompt.prompt_id
                            
                            updated = True
                if updated:
                    session.commit()
                else:
                    session.refresh(response)

                updated = (
                    session.query(Responses)
                    .options(joinedload(Responses.prompt), joinedload(Responses.lang))
                    .filter(Responses.response_id == response_id)
                    .first()
                )

                return updated

            except Exception as e:
                session.rollback()
                raise e



    def delete_response_record(self, response_id: int) -> bool:
        with self.Session() as session:
            response = (
                session.query(Responses)
                .filter(Responses.response_id == response_id)
                .first()
            )
            if not response:
                return False
            session.delete(response)
            session.commit()
            return True

    def create_strategy_v2(self, payload: dict) -> int:
        with self.Session() as session:
            if (
                session.query(Strategies)
                .filter_by(strategy_name=payload["strategy_name"])
                .first()
            ):
                raise IntegrityError(
                    "Strategy name already exists", params=None, orig=None
                )

            new_strategy = Strategies(
                strategy_name=payload["strategy_name"],
                strategy_description=payload.get("strategy_description"),
            )
            session.add(new_strategy)
            session.commit()
            session.refresh(new_strategy)
            return new_strategy.strategy_id

    def update_strategy_v2(self, strategy_id: int, updates: dict) -> Optional[dict]:
        """Updates a strategy similar to the v1 logic but returns a v2-style dict.

        This method is intentionally self-contained and does not depend on the
        FastAPI endpoints module to avoid circular imports.
        """

        with self.Session() as session:
            strategy = (
                session.query(Strategies)
                .filter(Strategies.strategy_id == strategy_id)
                .first()
            )
            if strategy is None:
                return None

            original_name = strategy.strategy_name

            # Name uniqueness validation (like v1)
            if (
                "strategy_name" in updates
                and updates["strategy_name"]
                and updates["strategy_name"] != original_name
            ):
                existing_strategy = (
                    session.query(Strategies)
                    .filter(Strategies.strategy_name == updates["strategy_name"])
                    .first()
                )
                if existing_strategy:
                    raise ValueError("Strategy name already exists")

            # Update fields if provided (like v1)
            updated = False
            if "strategy_name" in updates:
                strategy.strategy_name = updates["strategy_name"]
                updated = True
            if "strategy_description" in updates:
                strategy.strategy_description = updates["strategy_description"]
                updated = True

            # If nothing actually changed, mirror v1 early-return behaviour
            if not updated:
                strategy_ids_with_llm_prompt = self._get_strategy_ids_requiring_llm_prompt(session)
                return {
                    "strategy_id": strategy.strategy_id,
                    "strategy_name": strategy.strategy_name,
                    "strategy_description": strategy.strategy_description,
                    "requires_llm_prompt": strategy.strategy_id
                    in strategy_ids_with_llm_prompt,
                }

            session.commit()
            session.refresh(strategy)

            # Compute requires_llm_prompt after refresh (like v1)
            strategy_ids_with_llm_prompt = self._get_strategy_ids_requiring_llm_prompt(session)

            return {
                "strategy_id": strategy.strategy_id,
                "strategy_name": strategy.strategy_name,
                "strategy_description": strategy.strategy_description,
                "requires_llm_prompt": strategy.strategy_id
                in strategy_ids_with_llm_prompt,
            }

    def _get_strategy_ids_requiring_llm_prompt(self, session) -> set[int]:
        """Return IDs of strategies that have at least one testcase with a judge_prompt.

        This mirrors the helper used in the v2 strategy endpoint but keeps the
        logic local to the ORM layer to avoid depending on the API module.
        """

        return {
            strategy_id
            for (strategy_id,) in (
                session.query(TestCases.strategy_id)
                .filter(TestCases.judge_prompt_id.isnot(None))
                .distinct()
            )
            if strategy_id is not None
        }


    def delete_strategy_record(self, strategy_id: int) -> bool:
        with self.Session() as session:
            strategy = (
                session.query(Strategies)
                .filter(Strategies.strategy_id == strategy_id)
                .first()
            )
            if not strategy:
                return False

            # check if strategy is used in TestCases
            testcases_with_strategy = session.query(TestCases).filter(TestCases.strategy_id == strategy_id).all()
            if testcases_with_strategy:
                strategy_ids = [t.strategy_id for t in testcases_with_strategy]
                testcases_using_strategy = session.query(TestCases).filter(TestCases.strategy_id.in_(strategy_ids)).first()
                if testcases_using_strategy:
                    raise ValueError(
                        "This strategy cannot be deleted because it is used in the TestCase table."
                    )

            session.delete(strategy)
            session.commit()
            return True


    def create_target_v2(self, payload: dict) -> int:
        """
        Creates a new target in the database.
        """
        with self.Session() as session:
            if (
                session.query(Targets)
                .filter_by(target_name=payload["target_name"])
                .first()
            ):
                raise IntegrityError(
                    "Target name already exists", params=None, orig=None
                )

            domain_id = self.add_or_get_domain_id(payload["domain_name"])
            if domain_id == -1:
                raise ValueError("Failed to create or get domain")

            new_target = Targets(
                target_name=payload["target_name"],
                target_type=payload["target_type"],
                target_description=payload.get("target_description"),
                target_url=payload.get("target_url"),
                domain_id=domain_id,
            )

            if "lang_list" in payload:
                languages = (
                    session.query(Languages)
                    .filter(Languages.lang_name.in_(payload["lang_list"]))
                    .all()
                )
                new_target.langs = languages

            session.add(new_target)
            session.commit()
            session.refresh(new_target)
            return new_target.target_id

    def update_target_by_id(self, target_id: int, updates: dict) -> Optional[dict]:
        """
        Updates a target similar to v1 method but using v2 style.
        """
        with self.Session() as session:
            target = (
                session.query(Targets)
                .options(
                    joinedload(Targets.domain),
                    joinedload(Targets.langs)
                )
                .filter(Targets.target_id == target_id)
                .first()
            )
            if target is None:
                return None

            # Store original values for change detection (like v1)
            # original_name = target.target_name
            # original_type = target.target_type
            # original_description = target.target_description
            # original_url = target.target_url
            # original_domain_name = target.domain.domain_name if target.domain else None
            # original_lang_names = sorted([lang.lang_name for lang in target.langs]) if target.langs else []

            updated = False

            # URL uniqueness validation (like v1)
            if "target_url" in updates and updates["target_url"]:
                existing_url = (
                    session.query(Targets)
                    .filter(
                        Targets.target_url == updates["target_url"],
                        Targets.target_id != target_id
                    )
                    .first()
                )
                if existing_url:
                    raise ValueError("Target URL already exists")
                target.target_url = updates["target_url"]
                updated = True

            # Target name update (like v1)
            if "target_name" in updates and updates["target_name"]:
                existing_name =(
                    session.query(Targets)
                    .filter(
                        Targets.target_name == updates["target_name"],
                        Targets.target_id != target_id
                    )
                    .first()
                )
                if existing_name:
                    raise ValueError("Target name already exists")
                target.target_name = updates["target_name"]
                updated = True

            # Target type update (like v1)
            if "target_type" in updates and updates["target_type"]:
                target.target_type = updates["target_type"]
                updated = True

            # Target description update (like v1)
            if "target_description" in updates:
                target.target_description = updates["target_description"]
                updated = True

            # Domain update with create-if-not-exists (like v1)
            if "domain_name" in updates and updates["domain_name"]:
                domain = session.query(Domains).filter(Domains.domain_name == updates["domain_name"]).first()
                if domain is None:
                    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Domain not found")
                target.domain_id = domain.domain_id
                updated = True

            # Language list update with create-if-not-exists (like v1)
            if "lang_list" in updates and updates["lang_list"] is not None:
                updated_langs = []
                for lang_name in updates["lang_list"]:
                    lang = session.query(Languages).filter(Languages.lang_name == lang_name).first()
                    if lang is None:
                        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Language not found")
                    updated_langs.append(lang)
                target.langs = updated_langs
                updated = True

            if updated:
                session.commit()
                session.refresh(target)
            else:
                # Refresh even if no changes (like v1 behavior)
                session.refresh(target)

            return target


    def delete_target_record(self, target_id: int) -> bool:
        """
        Deletes a target by ID.
        """
        with self.Session() as session:
            target = (
                session.query(Targets).filter(Targets.target_id == target_id).first()
            )
            if target is None:
                return False
            session.delete(target)
            session.commit()
            return True

    def get_testcase_by_name(self, testcase_name: str) -> Optional[TestCase]:
        """
        Fetches a test case by its name.

        Args:
            testcase_name (str): The name of the test case to fetch.

        Returns:
            Optional[TestCase]: The TestCase object if found, otherwise None.
        """
        with self.Session() as session:
            sql = select(TestCases).where(TestCases.testcase_name == testcase_name)
            result = session.execute(sql).scalar_one_or_none()
            if result is None:
                self.logger.error(f"TestCase with name '{testcase_name}' does not exist.")
                return None
            # Return a TestCase object with the fetched data
            return TestCase(name=getattr(result, 'testcase_name'),
                            metric=result.metrics[0].metric_name,  # use the first metric associated with the test case
                            testcase_id=getattr(result, 'testcase_id'),
                            prompt=Prompt(prompt_id=getattr(result.prompt, 'prompt_id'),
                                          user_prompt=str(result.prompt.user_prompt),
                                          system_prompt=str(result.prompt.system_prompt),
                                          lang_id=getattr(result.prompt, 'lang_id')),
                            response=Response(response_text=str(result.response.response_text),
                                              response_type=result.response.response_type,
                                              response_id=getattr(result.response, 'response_id'),
                                              prompt_id=result.response.prompt_id,
                                              lang_id=result.response.lang_id,
                                              digest=result.response.hash_value) if result.response else None,
                            judge_prompt=LLMJudgePrompt(prompt=str(result.judge_prompt.prompt),
                                                        lang_id=getattr(result.judge_prompt, 'lang_id')) if result.judge_prompt else None,
                            strategy=result.strategy.strategy_name)


    def delete_target_record(self, target_id: int) -> bool:
        """
        Deletes a target by ID.
        """
        with self.Session() as session:
            target = (
                session.query(Targets).filter(Targets.target_id == target_id).first()
            )
            if target is None:
                return False
            session.delete(target)
            session.commit()
            return True

    def get_testcase_by_id(self, testcase_id: int) -> Optional[TestCase]:
        """
        Fetches a test case by its ID.
        
        Args:
            testcase_id (int): The ID of the test case to fetch.
        
        Returns:
            Optional[TestCase]: The TestCase object if found, otherwise None.
        """
        with self.Session() as session:
            sql = select(TestCases).where(TestCases.testcase_id == testcase_id)
            result = session.execute(sql).scalar_one_or_none()
            if result is None:
                self.logger.error(f"TestCase with ID '{testcase_id}' does not exist.")
                return None
            # Return a TestCase object with the fetched data
            return TestCase(name=getattr(result, 'testcase_name'),
                            metric=result.metrics[0].metric_name,  # use the first metric associated with the test case
                            testcase_id=getattr(result, 'testcase_id'),
                            prompt=Prompt(prompt_id=getattr(result.prompt, 'prompt_id'),
                                          user_prompt=str(result.prompt.user_prompt),
                                          system_prompt=str(result.prompt.system_prompt),
                                          lang_id=getattr(result.prompt, 'lang_id')),
                            response=Response(response_text=str(result.response.response_text),
                                              response_type=result.response.response_type,
                                              response_id=getattr(result.response, 'response_id'),
                                              prompt_id=result.response.prompt_id,
                                              lang_id=result.response.lang_id,
                                              digest=result.response.hash_value) if result.response else None,
                            judge_prompt=LLMJudgePrompt(prompt=str(result.judge_prompt.prompt),
                                                        lang_id=getattr(result.judge_prompt, 'lang_id')) if result.judge_prompt else None,
                            strategy=result.strategy.strategy_name)
        
    def get_testcase_name(self, testcase_id: int) -> Optional[str]:
        """
        Fetches the name of a test case by its ID.
        
        Args:
            testcase_id (int): The ID of the test case to fetch.
        
        Returns:
            Optional[str]: The name of the test case if found, otherwise None.
        """
        with self.Session() as session:
            sql = select(TestCases).where(TestCases.testcase_id == testcase_id)
            result = session.execute(sql).scalar_one_or_none()
            if result is None:
                self.logger.error(f"TestCase with ID '{testcase_id}' does not exist.")
                return None
            return getattr(result, 'testcase_name')
        
    def get_testcase_id(self, testcase_name: str) -> Optional[int]:
        """
        Fetches the ID of a test case by its name.
        
        Args:
            testcase_name (str): The name of the test case to fetch.
        
        Returns:
            Optional[int]: The ID of the test case if found, otherwise None.
        """
        with self.Session() as session:
            sql = select(TestCases).where(TestCases.testcase_name == testcase_name)
            result = session.execute(sql).scalar_one_or_none()
            if result is None:
                self.logger.error(f"TestCase with name '{testcase_name}' does not exist.")
                return None
            return getattr(result, 'testcase_id')
        
    def get_metric_by_id(self, metric_id: int) -> Optional[Metric]:
        """
        Fetches a metric by its ID.
        
        Args:
            metric_id (int): The ID of the metric to fetch.
        
        Returns:
            Optional[Metric]: The Metric object if found, otherwise None.
        """
        with self.Session() as session:
            sql = select(Metrics).where(Metrics.metric_id == metric_id)
            result = session.execute(sql).scalar_one_or_none()
            if result is None:
                self.logger.error(f"Metric with ID '{metric_id}' does not exist.")
                return None
            return Metric(metric_name=getattr(result, 'metric_name'),
                          domain_id=getattr(result, 'domain_id'),
                          metric_description=str(result.metric_description),
                          metric_id=getattr(result, 'metric_id'))
        
    def get_metric_name(self, metric_id: int) -> Optional[str]:
        """
        Fetches the name of a metric by its ID.
        
        Args:
            metric_id (int): The ID of the metric to fetch.
        
        Returns:
            Optional[str]: The name of the metric if found, otherwise None.
        """
        with self.Session() as session:
            sql = select(Metrics).where(Metrics.metric_id == metric_id)
            result = session.execute(sql).scalar_one_or_none()
            if result is None:
                self.logger.error(f"Metric with ID '{metric_id}' does not exist.")
                return None
            return getattr(result, 'metric_name')
        
    def get_metric_id(self, metric_name: str) -> Optional[int]:
        """
        Fetches the ID of a metric by its name.
        
        Args:
            metric_name (str): The name of the metric to fetch.
        
        Returns:
            Optional[int]: The ID of the metric if found, otherwise None.
        """
        with self.Session() as session:
            sql = select(Metrics).where(Metrics.metric_name == metric_name)
            result = session.execute(sql).scalar_one_or_none()
            if result is None:
                self.logger.error(f"Metric with name '{metric_name}' does not exist.")
                return None
            return getattr(result, 'metric_id')
        
    def get_testplan_name(self, plan_id: int) -> Optional[str]:
        """
        Fetches the name of a test plan by its ID.
        
        Args:
            plan_id (int): The ID of the test plan to fetch.
        
        Returns:
            Optional[str]: The name of the test plan if found, otherwise None.
        """
        with self.Session() as session:
            sql = select(TestPlans).where(TestPlans.plan_id == plan_id)
            result = session.execute(sql).scalar_one_or_none()
            if result is None:
                self.logger.error(f"TestPlan with ID '{plan_id}' does not exist.")
                return None
            return getattr(result, 'plan_name')
        
    def get_testplan_id(self, plan_name: str) -> Optional[int]:
        """
        Fetches the ID of a test plan by its name.
        
        Args:
            plan_name (str): The name of the test plan to fetch.
        
        Returns:
            Optional[int]: The ID of the test plan if found, otherwise None.
        """
        with self.Session() as session:
            sql = select(TestPlans).where(TestPlans.plan_name == plan_name)
            result = session.execute(sql).scalar_one_or_none()
            if result is None:
                self.logger.error(f"TestPlan with name '{plan_name}' does not exist.")
                return None
            return getattr(result, 'plan_id')
        
    def get_all_run_details_by_run_name(self, run_name:str) -> List[RunDetail]:
        """
        Fetches all run details for a specific run name.

        Args:
            run_name (str): The name of the run to fetch details for.

        Returns:
            List[RunDetail]: A list of RunDetail objects for the specified run name.
        """
        with self.Session() as session:
            sql = select(TestRunDetails).join(TestRuns).where(TestRuns.run_name == run_name)
            results = session.execute(sql).scalars().all()
            return [RunDetail(run_name=result.run.run_name,
                              testcase_name=result.testcase.testcase_name,
                              metric_name=result.metric.metric_name,
                              plan_name=result.plan.plan_name,
                              # unfortunately, as per the table design, 
                              # there can be more than one conversation per run_detail.
                              # in reality, that is restricted. 
                              #@NOTE: Try changing the table design by merging rundetails and conversations.
                              conversation_id = result.conversation[0].conversation_id,
                              status=getattr(result, "testcase_status"),
                              detail_id=result.detail_id) for result in results]

    def get_run_detail_by_id(self, detail_id: int) -> Optional[RunDetail]:
        """
        Fetches a test run detail by its ID.
        
        Args:
            detail_id (int): The ID of the test run detail to fetch.
        
        Returns:
            Optional[RunDetail]: The RunDetail object if found, otherwise None.
        """
        with self.Session() as session:
            sql = select(TestRunDetails).where(TestRunDetails.detail_id == detail_id)
            result = session.execute(sql).scalar_one_or_none()
            if result is None:
                self.logger.error(f"TestRunDetail with ID '{detail_id}' does not exist.")
                return None
            return RunDetail(run_name=result.run.run_name,
                             testcase_name=result.testcase.testcase_name,
                             metric_name=result.metric.metric_name,
                             plan_name=result.plan.plan_name,
                             status=getattr(result, "testcase_status"),
                             detail_id=detail_id)
        
    def add_or_update_testrun_detail(self, run_detail: RunDetail) -> int:
        """
        Adds a new test run detail to the database or fetches its ID if it already exists.
        
        Args:
            run_detail (RunDetail): The RunDetail object to be added.
        
        Returns:
            int: The ID of the newly added run detail, or -1 if it already exists.
        """
        try:
            # First, ensure the run exists and get its ID
            run_id = self.get_run_id(run_detail.run_name)
            if run_id is None:
                self.logger.error(f"Run with name '{run_detail.run_name}' does not exist. Cannot add run detail.")
                return -1
            
            testcase_id = self.get_testcase_id(run_detail.testcase_name)
            if testcase_id is None:
                self.logger.error(f"TestCase with name '{run_detail.testcase_name}' does not exist. Cannot add run detail.")
                return -1
            
            metric_id = self.get_metric_id(run_detail.metric_name)
            if metric_id is None:
                self.logger.error(f"Metric with name '{run_detail.metric_name}' does not exist. Cannot add run detail.")
                return -1
            
            plan_id = self.get_testplan_id(run_detail.plan_name)
            if plan_id is None:
                self.logger.error(f"TestPlan with name '{run_detail.plan_name}' does not exist. Cannot add run detail.")
                return -1

            with self.Session() as session:
                # Check if the run detail already exists in the database
                existing_run_detail = session.query(TestRunDetails).filter_by(run_id=run_id, testcase_id=testcase_id).first()
                if existing_run_detail:
                    # check if the status is the same or higher.
                    if self.__status_compare(run_detail.status, getattr(existing_run_detail, "testcase_status")) <= 0:
                        # If the run detail already exists and the status is the same or lower, return the existing detail ID
                        self.logger.debug(f"RunDetail for Run ID {run_id} and TestCase ID {testcase_id} already exists with status '{existing_run_detail.testcase_status}'. Returning existing detail ID: {existing_run_detail.detail_id}")
                        # Return the ID of the existing run detail
                        return getattr(existing_run_detail, "detail_id")
                    # If the run detail exists but the status is higher, we will update the existing run detail
                    self.logger.debug(f"RunDetail for Run ID {run_id} and TestCase ID {testcase_id} exists with status '{existing_run_detail.testcase_status}'. Updating existing detail with status '{run_detail.status}' ..")
                    # Update the existing run detail with the new status
                    setattr(existing_run_detail, "testcase_status", run_detail.status)
                    # Commit the session to save the updated run detail
                    session.commit()
                    # Ensure detail_id is populated
                    session.refresh(existing_run_detail)  
                    self.logger.debug(f"Returning the ID of the updated run detail: {existing_run_detail.detail_id}")
                    # Return the ID of the existing run detail
                    return getattr(existing_run_detail, "detail_id")

                # If the run detail does not exist, we will create a new one
                self.logger.debug(f"RunDetail for Run ID {run_id} and TestCase ID {testcase_id} does not exist. Creating a new one.")
                # forcing the status to be "NEW"
                run_detail.status = "NEW"
                
                self.logger.debug(f"Adding new RunDetail for Run (ID:{run_id}, {run_detail.run_name}), Plan (ID:{plan_id}, {run_detail.plan_name}), Metric (ID:{metric_id}, {run_detail.metric_name}), and TestCase (ID:{testcase_id}, {run_detail.testcase_name})")

                # Create the TestRunDetails object
                new_run_detail = TestRunDetails(run_id=run_id,
                                                testcase_id=testcase_id,
                                                testcase_status=run_detail.status,
                                                plan_id=plan_id,
                                                metric_id=metric_id)
                
                # Add the new run detail to the session
                session.add(new_run_detail)
                # Commit the session to save the new run detail
                session.commit()
                # Ensure detail_id is populated
                session.refresh(new_run_detail)  

                self.logger.debug(f"RunDetail added successfully: {new_run_detail.detail_id}")
                
                # Return the ID of the newly added run detail
                return getattr(new_run_detail, "detail_id")
        except IntegrityError as e:
            # Handle the case where the run detail already exists
            self.logger.error(f"RunDetail already exists: {run_detail}. Error: {e}")
            return -1
        
    def get_run_detail_status(self, run_name: str, testcase_name: str) -> Optional[str]:
        """
        Fetches the status of a run detail based on the run name and test case name.
        
        Args:
            run_name (str): The name of the run to fetch the detail for.
            testcase_name (str): The name of the test case to fetch the detail for.
        
        Returns:
            Optional[str]: The status of the run detail if found, otherwise None.
        """
        with self.Session() as session:
            self.logger.debug(f"Fetching RunDetail status for Run '{run_name}' and TestCase '{testcase_name}' ..")
            sql = select(TestRunDetails).join(TestRuns, TestRunDetails.run_id == TestRuns.run_id) \
                                         .join(TestCases, TestRunDetails.testcase_id == TestCases.testcase_id) \
                                         .where(TestRuns.run_name == run_name, TestCases.testcase_name == testcase_name)
            result = session.execute(sql).scalar_one_or_none()
            if result is None:
                self.logger.error(f"RunDetail for Run '{run_name}' and TestCase '{testcase_name}' does not exist.")
                return None
            return getattr(result, 'testcase_status')
        
    def get_status_by_run_name(self, run_name: str) -> Optional[str]:
        """
        Fetches the status of a test run based on its name.
        
        Args:
            run_name (str): The name of the test run to fetch the status for.
        
        Returns:
            Optional[str]: The status of the test run if found, otherwise None.
        """
        with self.Session() as session:
            self.logger.debug(f"Fetching status for TestRun with name: {run_name}")
            sql = select(TestRuns).where(TestRuns.run_name == run_name)
            result = session.execute(sql).scalar_one_or_none()
            if result is None:
                self.logger.error(f"TestRun with name '{run_name}' does not exist.")
                return None
            return getattr(result, 'status')
        
    def get_status_by_run_id(self, run_id: int) -> Optional[str]:
        """
        Fetches the status of a test run based on its ID.
        
        Args:
            run_id (int): The ID of the test run to fetch the status for.
        
        Returns:
            Optional[str]: The status of the test run if found, otherwise None.
        """
        with self.Session() as session:
            # Fetch the TestRuns object based on the run_id
            self.logger.debug(f"Fetching status for TestRun with ID: {run_id}")
            sql = select(TestRuns).where(TestRuns.run_id == run_id)
            result = session.execute(sql).scalar_one_or_none()
            if result is None:
                self.logger.error(f"TestRun with ID '{run_id}' does not exist.")
                return None
            return getattr(result, 'status')
        
    def get_status_by_run_detail_id(self, run_detail_id: int) -> Optional[str]:
        """
        Fetches the status of a test run detail based on its ID.
        
        Args:
            run_detail_id (int): The ID of the test run detail to fetch the status for.
        
        Returns:
            Optional[str]: The status of the test run detail if found, otherwise None.
        """
        with self.Session() as session:
            # Fetch the TestRunDetails object based on the run_detail_id
            # and return the testcase_status attribute.
            self.logger.debug(f"Fetching status for TestRunDetail with ID: {run_detail_id}")
            sql = select(TestRunDetails).where(TestRunDetails.detail_id == run_detail_id)
            result = session.execute(sql).scalar_one_or_none()
            if result is None:
                self.logger.error(f"TestRunDetail with ID '{run_detail_id}' does not exist.")
                return None
            return getattr(result, 'testcase_status')
        
    def add_or_update_conversation(self, conversation: Conversation, override:bool = False) -> int:
        """
        Adds a new conversation to the database or fetches its ID if it already exists.
        Updates the conversation with the agent response and time stamps, if it already exists.
        
        Args:
            conversation (Conversation): The Conversation object to be added.
        
        Returns:
            int: The ID of the newly added conversation, or -1 if it already exists.
        """
        try:
            target_id = self.get_target_id(conversation.target) if conversation.target else None
            if target_id is None:
                self.logger.error(f"Target '{conversation.target}' does not exist. Cannot add conversation.")
                return -1
            
            with self.Session() as session:
                # Check if the conversation already exists in the database
                existing_conversation = session.query(Conversations).filter_by(detail_id=conversation.run_detail_id).first()
                if existing_conversation:
                    # update the evaluation details
                    if (existing_conversation.evaluation_ts is None or override) and conversation.evaluation_ts is not None:
                        if existing_conversation.agent_response is None:
                            self.logger.error(f"Cannot update evaluation details for Conversation (RunDetailId:{conversation.run_detail_id}) as the agent response is not yet recorded.")
                            return -1
                        
                        if not override:
                            self.logger.debug(f"Updating existing conversation details (Evaluation score: {conversation.evaluation_score}, reason and timestamp: {conversation.evaluation_ts}) ..")
                        else:
                            self.logger.debug(f"Overwriting existing conversation details (Evaluation score: {conversation.evaluation_score}, reason and timestamp: {conversation.evaluation_ts}) ..")                            
                            
                        # Update the existing conversation with the new details
                        setattr(existing_conversation, "evaluation_score", conversation.evaluation_score)
                        setattr(existing_conversation, "evaluation_reason", conversation.evaluation_reason)
                        setattr(existing_conversation, "evaluation_ts", self._ensure_datetime(conversation.evaluation_ts))
                    # update the agent response details.
                    else:
                        if existing_conversation.prompt_ts is None and conversation.prompt_ts is not None:
                            self.logger.debug(f"Updating existing conversation details (Prompt timestamp: {conversation.prompt_ts}) ..")
                        elif existing_conversation.agent_response is None and conversation.agent_response is not None:
                            self.logger.debug(f"Updating existing conversation details (Agent response text and Response timestamp: {conversation.response_ts}) ..")
                        elif existing_conversation.response_ts is None and conversation.response_ts is not None:
                            self.logger.debug(f"Updating existing conversation details (Agent response text and Response timestamp: {conversation.response_ts}) ..")
                        elif override:
                            self.logger.debug(f"Updating existing conversation details with the supplied 'override' information. (RunDetailId:{conversation.run_detail_id}) ..")
                        else:
                            self.logger.debug(f"Existing conversation (RunDetailId:{conversation.run_detail_id}) will not be updated. Returning conversation ID: {existing_conversation.conversation_id}")
                            # Return the ID of the existing conversation if it already exists
                            return getattr(existing_conversation, "conversation_id")

                        # Update the existing conversation with the new details
                        setattr(existing_conversation, "agent_response", conversation.agent_response)
                        setattr(existing_conversation, "prompt_ts", self._ensure_datetime(conversation.prompt_ts))
                        setattr(existing_conversation, "response_ts", self._ensure_datetime(conversation.response_ts))
                    
                    # Commit the session to save the updated conversation
                    session.commit()
                    # Ensure conversation_id is populated
                    session.refresh(existing_conversation)   
                    # Log the existing conversation ID
                    self.logger.debug(f"Returning the ID of the updated conversation: {existing_conversation.conversation_id}")
                    # Return the ID of the existing conversation
                    return getattr(existing_conversation, "conversation_id")
                
                self.logger.debug(f"Adding a new conversation with run detail ID: {conversation.run_detail_id}")

                # Create the Conversations object
                new_conversation = Conversations(
                                                target_id=target_id,
                                                detail_id=conversation.run_detail_id,
                                                agent_response=conversation.agent_response,
                                                prompt_ts=self._ensure_datetime(conversation.prompt_ts),
                                                response_ts=self._ensure_datetime(conversation.response_ts),
                                                evaluation_score=conversation.evaluation_score,
                                                evaluation_reason=conversation.evaluation_reason,
                                                evaluation_ts=self._ensure_datetime(conversation.evaluation_ts)
                                            )


                # Add the new conversation to the session
                session.add(new_conversation)
                # Commit the session to save the new conversation
                session.commit()
                # Ensure conversation_id is populated
                session.refresh(new_conversation)  

                self.logger.debug(f"Conversation added successfully: {new_conversation.conversation_id}")
                
                # Return the ID of the newly added conversation
                return getattr(new_conversation, "conversation_id")
        except IntegrityError as e:
            # Handle the case where the conversation already exists
            self.logger.error(f"Conversation already exists: {conversation}. Error: {e}")
            return -1

    def get_conversation_by_id(self, conversation_id: int) -> Optional[Conversation]:
        """
        Fetches a conversation by its ID.
        
        Args:
            conversation_id (int): The ID of the conversation to fetch.
        
        Returns:
            Optional[Conversation]: The Conversation object if found, otherwise None.
        """
        with self.Session() as session:
            sql = select(Conversations).where(Conversations.conversation_id == conversation_id)
            result = session.execute(sql).scalar_one_or_none()
            if result is None:
                self.logger.error(f"Conversation with ID '{conversation_id}' does not exist.")
                return None
            return Conversation(target=result.target.target_name,
                                run_detail_id=getattr(result, "detail_id"),
                                testcase=result.detail.testcase.testcase_name,
                                agent_response=getattr(result, "agent_response"),
                                prompt_ts=result.prompt_ts.isoformat() if getattr(result, "prompt_ts") else None,
                                response_ts=result.response_ts.isoformat() if getattr(result, "response_ts") else None,
                                evaluation_score=getattr(result, "evaluation_score"),
                                evaluation_reason=getattr(result, "evaluation_reason"),
                                evaluation_ts=result.evaluation_ts.isoformat() if getattr(result, "evaluation_ts") else None,
                                conversation_id=getattr(result, 'conversation_id'))
        
    def get_agent_responses_by_run_name(self, run_name:str) -> List[Conversation]:
        """
        Fetches all agent responses for a given run name.
        
        Args:
            run_name (str): The name of the run to fetch agent responses for.
        
        Returns:
            List[Conversation]: A list of Conversation objects containing agent responses.
        """
        with self.Session() as session:
            sql = select(Conversations).join(TestRunDetails, Conversations.detail_id == TestRunDetails.detail_id) \
                                       .join(TestRuns, TestRunDetails.run_id == TestRuns.run_id) \
                                       .where(TestRuns.run_name == run_name)
            results = session.execute(sql).scalars().all()
            return [Conversation(target=result.target.target_name,
                                 run_detail_id=getattr(result, "detail_id"),
                                 testcase=result.detail.testcase.testcase_name,
                                 agent_response=getattr(result, "agent_response"),
                                 prompt_ts=result.prompt_ts.isoformat() if getattr(result, "prompt_ts") else None,
                                 response_ts=result.response_ts.isoformat() if getattr(result, "response_ts") else None,
                                 evaluation_score=getattr(result, "evaluation_score"),
                                 evaluation_reason=getattr(result, "evaluation_reason"),
                                 evaluation_ts=getattr(result, "evaluation_ts"),
                                 conversation_id=getattr(result, 'conversation_id')) for result in results]

    # Back-end router functions
    def get_username_from_token(authorization: Optional[str]) -> Optional[str]:
        """Extract username from JWT token."""
        if not authorization:
            return None
        
        try:
            scheme, token = authorization.split()
            if scheme.lower() != "bearer":
                return None
        except ValueError:
            return None
        
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            return payload.get("user_name")
        except JWTError:
            return None