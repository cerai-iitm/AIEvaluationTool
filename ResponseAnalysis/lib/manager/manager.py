class Analyzer:
    def __init__(self) -> None:
        pass

from multipledispatch import dispatch

@dispatch(str, str)
def analyze(file_path: str, output_path: str) -> None:
    """
    Analyze the file at the given path and save the results to the output path.
    
    :param file_path: Path to the input file to be analyzed.
    :param output_path: Path where the analysis results will be saved.
    """
    # Placeholder for actual analysis logic
    print(f"Analyzing {file_path} and saving results to {output_path}")

@dispatch(str, str, str)
def analyze(file_path: str, output_path: str, additional_param: str) -> None:
    """
    Analyze the file at the given path with an additional parameter and save the results to the output path.
    
    :param file_path: Path to the input file to be analyzed.
    :param output_path: Path where the analysis results will be saved.
    :param additional_param: An additional parameter for analysis.
    """
    # Placeholder for actual analysis logic with additional parameter
    print(f"Analyzing {file_path} with {additional_param} and saving results to {output_path}")

def main2():
    # Example usage of the analyze function
    analyze("input.txt", "output.txt")
    analyze("input.txt", "output.txt", "extra_param")

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session, relationship
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select

from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import Column, Integer, Text, DateTime, String, Enum, ForeignKey

class Base(DeclarativeBase):
    __abstract__ = True
    """Base class for all ORM models.
    This class serves as a base for all ORM models in the application.
    It inherits from DeclarativeBase, which is a base class for declarative models in SQLAlchemy.
    It can be extended to include common functionality or properties for all models.
    """
    id = Column(Integer, primary_key=True, autoincrement=True)

class Address(Base):
    """ORM model for the Address table.
    This class defines the structure of the Address table in the database.
    """
    __tablename__ = 'Addresses'
    
    state = Column(String(100), nullable=False)
    zip_code = Column(String(20), nullable=False)
    user_id = Column(Integer, ForeignKey('Users.id'), nullable=False)  # Foreign key to Users
    user = relationship("User", back_populates="addresses")

    def __repr__(self) -> str:
        return f"Address(state={self.state!r}, zip_code={self.zip_code!r})"

class User(Base):
    """ORM model for the User table.
    This class defines the structure of the User table in the database.
    """
    __tablename__ = 'Users'
    
    username = Column(String(50), nullable=False, unique=True)
    age = Column(Integer, nullable=False)
    addresses = relationship("Address") #, back_populates="user", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"User(username={self.username!r}, age={self.age!r}, addresses={self.addresses!r})"


engine = create_engine("mariadb+mariadbconnector://root:ATmega32*@localhost:3306/aieval", echo=True, pool_size=10, max_overflow=30)
# Create all tables in the database
# This will create the tables defined in the ORM models if they do not exist.
Base.metadata.create_all(engine)
# Create a scoped session to manage database sessions
# A scoped session is a thread-safe session that can be used across multiple threads.
#session = scoped_session(sessionmaker(bind=engine))

a1 = Address(state="California", zip_code="90001")
a2 = Address(state="New York", zip_code="10001")
a3 = Address(state="Texas", zip_code="73301")

u1 = User(username="john_doe", age=30)
u2 = User(username="jane_doe", age=25)

u1.addresses.extend([a1, a2])
u2.addresses.append(a3)

Session = sessionmaker(bind=engine)
session = Session()
try:
    session.add(u1)
    session.add(u2)
    session.commit()
except IntegrityError as e:
    session.rollback()
    print(f"IntegrityError: {e}")
    session.close()    

u1.addresses

#if __name__ == "__main__":
#    main()
    # This will run the main function when the script is executed directly
    # If this module is imported, the main function will not run automatically
    # This is a common practice to allow the module to be used both as a script and as an importable module.