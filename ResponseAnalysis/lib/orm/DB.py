from tables import Base, Languages, Domains, Metrics, Responses, TestCases, TestPlans, Prompts
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy import select
from typing import List, Optional, Union
from ..data.prompt import Prompt

class DB:    
    """
    Database connection and session management class.
    This class provides methods to create a database engine, session, and manage the connection lifecycle.
    It uses SQLAlchemy for ORM and supports MariaDB as the database backend.
    """

    def __init__(self, db_url: str = "mariadb+mariadbconnector://root:ATmega32*@localhost:3306/aieval"):
        """
        Initializes the DB instance with the provided database URL and host.
        
        Args:
            db_url (str): The database URL for connecting to the MariaDB database.
            host (str): The host where the MariaDB server is running.
        """
        self.db_url = db_url
        self.engine = create_engine(self.db_url, echo=True, pool_size=5, max_overflow=10)
        Base.metadata.create_all(self.engine)
        self.Session = scoped_session(sessionmaker(bind=self.engine))

    def sample_prompts(self, 
                       lang_id: Optional[int] = None, 
                       domain: Union[Optional[int], Optional[str]] = None,  # can be the domain id or name.
                       plan: Optional[Union[int, str]] = None,  # can be the plan id or name.
                       metric_id: Optional[int] = None ) -> List[Prompt]:
        """
        Fetches a sample of prompts from the database adhering to the specified filters.
        
        Returns:
            List[Prompts]: A list of Prompts objects.
        """
        with self.Session() as session:
            sql = select(Prompts).
            return session.query(Languages).all()