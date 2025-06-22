from tables import Base, Languages, Domains, Metrics, Responses, TestCases, TestPlans, Prompts, Strategies, LLMJudgePrompts
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select
from typing import List, Optional, Union
import sys
import os
import hashlib # For hashing prompts
import logging

# setup the relative import path for data module.
sys.path.append(os.path.dirname(__file__) + '/..')

from data import Prompt, Language, Domain, Response, TestCase, TestPlan, \
    Strategy, Metric, LLMJudgePrompt

class DB:    
    """
    Database connection and session management class.
    This class provides methods to create a database engine, session, and manage the connection lifecycle.
    It uses SQLAlchemy for ORM and supports MariaDB as the database backend.
    """

    def __init__(self, db_url: str, debug:bool, pool_size:int = 5, max_overflow:int = 10):
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
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)
        # Console handler
        ch = logging.StreamHandler()
        ch.setLevel(logging.DEBUG)
        ch_formatter = logging.Formatter("%(asctime)s|%(name)s|%(levelname)s|%(funcName)s|%(message)s")
        ch.setFormatter(ch_formatter)
        self.logger.addHandler(ch)

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
            sql = select(Strategies)
            return [Strategy(name=getattr(strategy, 'strategy_name'), 
                             description=getattr(strategy, 'strategy_description'),
                             strategy_id=getattr(strategy, 'strategy_id')) for strategy in session.query(Strategies).all()]
        return None
    
    def get_strategy_id(self, strategy_name: str) -> Optional[int]:
        """
        Fetches the ID of a strategy by its name.
        
        Args:
            strategy_name (str): The name of the strategy to fetch.
        
        Returns:
            Optional[int]: The ID of the strategy if found, otherwise None.
        """
        with self.Session() as session:
            sql = select(Strategies).where(Strategies.strategy_name == strategy_name)
            result = session.execute(sql).scalar_one_or_none()
            return getattr(result, 'strategy_id', None) if result else None
        
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
            return getattr(result, 'strategy_name', None) if result else None

    def add_language(self, lang_name: str) -> Optional[int]:
        with self.Session() as session:
            new_lang = Languages(lang_name=lang_name)
            try:
                session.add(new_lang)
                session.commit()
                # Ensure lang_id is populated
                session.refresh(new_lang)  
                self.logger.debug(f"Language added successfully: {new_lang.lang_id}")
                
                # Return the ID of the newly added response
                return getattr(new_lang, "lang_id")
            except IntegrityError as e:
                self.logger.error(f"Language '{lang_name}' already exists. Error: {e}")
                return None

    def get_language_id(self, lang_name: str) -> Optional[int]:
        """
        Fetches the ID of a language by its name.
        
        Args:
            lang_name (str): The name of the language to fetch.
        
        Returns:
            Optional[int]: The ID of the language if found, otherwise None.
        """
        with self.Session() as session:
            sql = select(Languages).where(Languages.lang_name == lang_name)
            result = session.execute(sql).scalar_one_or_none()
            return getattr(result, 'lang_id', None) if result else None
            #return result.lang_id if result else None
    
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
        
    def add_domain(self, domain_name: str) -> Optional[int]:
        """
        Adds a new domain to the database.
        
        Args:
            domain_name (str): The name of the domain to be added.
        
        Returns:
            Optional[int]: The ID of the newly added domain, or None if it already exists.
        """
        try:
            with self.Session() as session:
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
                testcase_strategy = result[2].strategy_id
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
                                testcase_id=testcase_id,
                                prompt=prompt,
                                prompt_id=prompt.prompt_id,
                                strategy=testcase_strategy,
                                response=response,
                                response_id=response_id)
            
            self.logger.error(f"Test case '{testcase}' does not exist.")
            return None
    
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
            strategy_id = self.get_strategy_id(strategy)
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
            strategy_id = self.get_strategy_id(strategy)
            if strategy_id is None:
                self.logger.error(f"Strategy '{strategy}' does not exist.")
                return -1

        try:
            # Add the prompt to the database and get its ID
            prompt_id = self.add_prompt(prompt)  
            if prompt_id == -1:
                self.logger.error(f"Prompt '{prompt.user_prompt}' already exists. Cannot create test case.")
                return -1
            
            # If a response is provided, create a Responses object
            response_id = self.add_response(response, prompt_id) if response else None

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
        
    def add_response(self, response: Response, prompt_id: int) -> int:
        """
        Adds a new response to the database.
        
        Args:
            response (Response): The Response object to be added.
        
        Returns:
            int: The ID of the newly added response, or -1 if it already exists.
        """
        try:
            with self.Session() as session:
                # Default to the default language ID if not provided
                lang_id = response.kwargs.get("lang_id", Language.autodetect)  # Get the language ID from kwargs if provided

                # create the orm object for the response to insert into the database table.
                new_response = Responses(response_text=response.response_text, 
                                         response_type=response.response_type,
                                         prompt_id=prompt_id,  # Get the prompt ID
                                         lang_id=lang_id,
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
            return LLMJudgePrompt(judge_prompt=str(result.judge_prompt),
                                  lang_id=getattr(result, 'lang_id', Language.autodetect),  # Get the language ID from kwargs if provided
                                  digest=result.hash_value)
        
    def add_or_get_judge_prompt(self, judge_prompt: LLMJudgePrompt) -> int:
        """
        Adds a new judge prompt to the database.
        
        Args:
            judge_prompt (LLMJudgePrompt): The LLMJudgePrompt object to be added.
        
        Returns:
            int: The ID of the newly added judge prompt, or -1 if it already exists.
        """
        try:
            with self.Session() as session:
                # check of the judge prompt already exists in the database.
                existing_judge_prompt = session.query(LLMJudgePrompts).filter_by(hash_value=judge_prompt.digest).first()
                if existing_judge_prompt:
                    # Return the ID of the existing judge prompt
                    return getattr(existing_judge_prompt, "prompt_id")
                    
                self.logger.debug(f"Adding new judge prompt: {judge_prompt.judge_prompt}")
                # create the orm object for the judge prompt to insert into the database table.
                new_judge_prompt = LLMJudgePrompts(prompt_text=judge_prompt.judge_prompt, 
                                                   lang_id=getattr(judge_prompt, "lang_id", Language.autodetect),  # Get the language ID from kwargs if provided
                                                   hash_value=judge_prompt.digest)
                
                # Add the new judge prompt to the session
                session.add(new_judge_prompt)
                # Commit the session to save the new judge prompt
                session.commit()
                # Ensure judge_prompt_id is populated
                session.refresh(new_judge_prompt)  

                self.logger.debug(f"Judge prompt added successfully: {new_judge_prompt.prompt_id}")
                
                # Return the ID of the newly added judge prompt
                return getattr(new_judge_prompt, "prompt_id")
        except IntegrityError as e:
            # Handle the case where the judge prompt already exists
            self.logger.error(f"Judge prompt already exists: {judge_prompt}. Error: {e}")
            return -1
    
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
                          digest=result.hash_value)

    def add_or_get_prompt(self, prompt: Prompt) -> int:
        """
        Adds a new prompt to the database.
        
        Args:
            prompt (Prompt): The Prompt object to be added.
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
                
                # Add each test case associated with the metric
                for testcase in testcases:
                    # Ensure the prompt is added first
                    prompt_id = self.add_prompt(testcase.prompt)
                    if prompt_id == -1:
                        self.logger.error(f"Prompt '{testcase.prompt.user_prompt}' already exists. Cannot add test case.")
                        return False
                    
                    judge_prompt_id = self.add_judge_prompt(testcase.judge_prompt) if testcase.judge_prompt else None
                    if judge_prompt_id == -1:
                        self.logger.error(f"Judge prompt '{testcase.judge_prompt.judge_prompt}' already exists. Cannot add test case.")
                        return False
                    
                    # If a response is provided, create a Responses object
                    response_id = self.add_response(testcase.response, prompt_id) if testcase.response else None
                    # If the response already exists, use its ID
                    if response_id == -1:
                        self.logger.error(f"Response '{testcase.response.response_text}' already exists. Cannot add test case.")
                        return False
                    
                    # Create the TestCases object
                    new_testcase = TestCases(testcase_name=testcase.name, 
                                             prompt_id=prompt_id, 
                                             response_id=response_id,
                                             strategy_id=testcase.strategy,
                                             metric=new_metric)  # Associate the metric with the test case
                    
                    # Add the new test case to the session
                    session.add(new_testcase)
                
                # Add the new metric to the session
                session.add(new_metric)
                # Commit the session to save all changes
                session.commit()
                
                self.logger.debug(f"Metric '{metric.metric_name}' and its test cases added successfully.")
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
                metric = Metrics(metric_name=metric_name, domain_id=domain_id, metric_description=metric_description)
                session.add(metric)
                session.commit()
            return metric