from tables import Base, Languages, Domains, Metrics, Responses, TestCases, TestPlans, Prompts
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

from data.prompt import Prompt
from data.language import Language
from data.domain import Domain
from data.response import Response

class DB:    
    """
    Database connection and session management class.
    This class provides methods to create a database engine, session, and manage the connection lifecycle.
    It uses SQLAlchemy for ORM and supports MariaDB as the database backend.
    """

    def __init__(self, db_url: str = "mariadb+mariadbconnector://root:ATmega32*@localhost:3306/aieval", debug=False, pool_size = 5, max_overflow = 10):
        """
        Initializes the DB instance with the provided database URL and host.
        
        Args:
            db_url (str): The database URL for connecting to the MariaDB database.
            host (str): The host where the MariaDB server is running.
        """
        self.db_url = db_url
        self.engine = create_engine(self.db_url, echo=debug, pool_size=pool_size, max_overflow=max_overflow)
        Base.metadata.create_all(self.engine)
        self.Session = scoped_session(sessionmaker(bind=self.engine))

        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)
        # Console handler
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        ch_formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")
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
        
    def create_test_plan(self, plan_name: str, plan_desc: str = "", **kwargs) -> bool:
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
        
    def create_testcase(self, testcase_name:str, prompt: Prompt, response: Optional[Response] = None) -> int:
        """
        Creates a new test case in the database.
        
        Args:
            prompt (Prompt): The prompt associated with the test case.
            response (Optional[str]): The response associated with the test case.
            kwargs: Additional keyword arguments for future extensibility.
        
        Returns:
            bool: True if the test case was created successfully, False if it already exists.
        """
        try:
            # Add the prompt to the database and get its ID
            prompt_id = self.add_prompt(prompt)  
            if prompt_id == -1:
                self.logger.error(f"Prompt '{prompt.user_prompt}' already exists. Cannot create test case.")
                return -1
            
            # If a response is provided, create a Responses object
            response_id = self.add_response(response, prompt_id) if response else None

            with self.Session() as session:
                self.logger.debug(f"Creating test case for prompt '{prompt.user_prompt}' ..")

                new_testcase = TestCases(testcase_name=testcase_name,  # Use the test case name
                                         prompt_id=prompt_id,  # Use the ID of the added prompt
                                         response_id=response_id) # Use the ID of the added response
                # Add the new test case to the session
                session.add(new_testcase)
                
                # Commit the session to save all changes
                session.commit()
                self.logger.debug(f"Test case created successfully for prompt '{new_testcase.testcase_id}'.")
                return getattr(new_testcase, "test_case_id")
            
        except IntegrityError as e:
            self.logger.error(f"Test case for prompt '{prompt.user_prompt}' already exists. Error: {e}")
            return -1
        
    def add_prompts(self, prompts: List[Prompt]) -> bool:
        """
        Adds multiple prompts to the database.
        
        Args:
            prompts (List[Prompt]): A list of Prompt objects to be added.
        
        Returns:
            bool: True if all prompts were added successfully, False if any prompt already exists.
        """
        try:
            with self.Session() as session:
                n_prompts = len(prompts)
                self.logger.debug(f"Adding {n_prompts} prompts to the database.")
                n_added = 0
                for prompt in prompts:
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
                    n_added += 1
                # Commit the session to save all new prompts
                session.commit()
                self.logger.debug(f"{n_added} prompts added successfully.")
                return True
        except IntegrityError as e:
            # Handle the case where one or more prompts already exist
            self.logger.error(f"One or more prompts already exist. Error: {e}")
            return False
        
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
    
    def add_prompt(self, prompt: Prompt) -> int:
        """
        Adds a new prompt to the database.
        
        Args:
            prompt (Prompt): The Prompt object to be added.
        """
        try:
            with self.Session() as session:
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
            self.logger.error(f"Prompt already exists: {prompt}. Error: {e}")
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
