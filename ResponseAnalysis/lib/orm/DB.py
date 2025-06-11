from tables import Base, Languages, Domains, Metrics, Responses, TestCases, TestPlans, Prompts
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy import select
from typing import List, Optional, Union
import sys
import os

# setup the relative import path for data module.
sys.path.append(os.path.dirname(__file__) + '/..')

from data.prompt import Prompt
from data.language import Language
from data.domain import Domain

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
        
    def add_prompt(self, prompt: Prompt) -> None:
        """
        Adds a new prompt to the database.
        
        Args:
            prompt (Prompt): The Prompt object to be added.
        """
        with self.Session() as session:
            # Default to the default language ID if not provided
            lang_id = prompt.kwargs.get("lang_id", Language.autodetect)  # Get the language ID from kwargs if provided

            new_prompt = Prompts(prompt_string=prompt.user_prompt, 
                                 system_prompt=prompt.system_prompt, 
                                 lang_id=lang_id)
            session.add(new_prompt)
            session.commit()

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
                    sql = sql.where(Prompts.plan_id == plan)
            if metric_id is not None:
                sql = sql.join(Metrics).where(Metrics.metric_id == metric_id)
            
            # Execute the query and return the results
            result = session.execute(sql).scalars().all()
            return [Prompt(prompt_id=prompt.prompt_id, 
                           prompt_string=prompt.prompt_string, 
                           system_prompt=prompt.system_prompt, 
                           lang_id=prompt.lang_id) for prompt in result]            
