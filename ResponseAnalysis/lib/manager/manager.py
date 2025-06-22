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
    
class TestPlans(Base):
    """ORM model for the TestPlans table.
    This class defines the structure of the TestPlans table in the database.
    """
    __tablename__ = 'TestPlans'
    
    plan_name = Column(String(255), nullable=False, unique=True)  # Unique name for the test plan
    plan_description = Column(Text, nullable=True)  # Optional description for the test plan

    metrics = relationship("Metrics", secondary="TestPlanMetricMapping", back_populates="plans")
    
    def __repr__(self) -> str:
        return f"TestPlans(plan_name={self.plan_name})"

class Metrics(Base):
    """ORM model for the Metrics table.
    This class defines the structure of the Metrics table in the database.
    """
    __tablename__ = 'Metrics'
    
    metric_name = Column(String(255), nullable=False, unique=True)
    metric_source = Column(String(255), nullable=True)
    metric_benchmark = Column(String(255), nullable=True)

    #plan_id = Column(Integer, ForeignKey('TestPlans.id'), nullable=False)
    plans = relationship("TestPlans", secondary="TestPlanMetricMapping", back_populates="metrics")

    def __repr__(self) -> str:
        return f"Metrics(metric_name={self.metric_name})"
    
class TestPlanMetricMapping(Base):
    """ORM model for the TestPlanMetricMapping table.
    This class defines the structure of the TestPlanMetricMapping table in the database.
    It maps test plans to metrics.
    """
    __tablename__ = 'TestPlanMetricMapping'
    
    plan_id = Column(Integer, ForeignKey('TestPlans.id'), nullable=False)  # Foreign key to TestPlans
    metric_id = Column(Integer, ForeignKey('Metrics.id'), nullable=False)  # Foreign key to Metrics


engine = create_engine("mariadb+mariadbconnector://root:ATmega32*@localhost:3306/test", echo=True, pool_size=10, max_overflow=30)
# Create all tables in the database
# This will create the tables defined in the ORM models if they do not exist.
Base.metadata.create_all(engine)
# Create a scoped session to manage database sessions
# A scoped session is a thread-safe session that can be used across multiple threads.
#session = scoped_session(sessionmaker(bind=engine))

# Create or get Metrics objects from the database to ensure they are persistent
def get_or_create_metric(session, metric_name):
    metric = session.query(Metrics).filter_by(metric_name=metric_name).first()
    if not metric:
        metric = Metrics(metric_name=metric_name)
        session.add(metric)
        session.commit()
    return metric

m4 = Metrics(metric_name="m4", metric_source="source4", metric_benchmark="benchmark4")
p3 = TestPlans(plan_name="p3", plan_description="Test plan for p3")

Session = sessionmaker(bind=engine)
session = Session()
try:
    # Fetch the existing TestPlans object from the database
    existing_plan = session.query(TestPlans).filter_by(plan_name="p3").first()
    if existing_plan:
        # Assign only persistent Metrics objects
        m1_db = session.query(Metrics).filter_by(metric_name="m1").first()
        m2_db = session.query(Metrics).filter_by(metric_name="m2").first()
        existing_plan.metrics = [m1_db, m2_db, m4]  # Add m4 to the existing plan's metrics
        # No need to add existing_plan again; just commit
    else:
        # If not found, create a new one and add it
        session.add(p3)
    session.commit()
except IntegrityError as e: 
    session.rollback()
    print(f"IntegrityError: {e}")
    session.close()    

"""
        # Example: Remove m4 from existing_plan.metrics if it exists
        #if existing_plan and m4 in existing_plan.metrics:
        #    existing_plan.metrics.remove(m4)
        #    session.add(existing_plan)


    #session.add_all([m1, m2, m3, p1, p2])
    session.commit()
except IntegrityError as e: 
    session.rollback()
    print(f"IntegrityError: {e}")
    session.close()    
"""

tp = session.query(TestPlans).first()
mets = [metric.metric_name for metric in getattr(tp, "metrics")]
print(",".join(mets))

met = session.query(Metrics).first()
plans = [plan.plan_name for plan in getattr(met, "plans")]
print(",".join(plans))

out = session.query(Metrics).filter(Metrics.plans.any(plan_name="p2")).all()
print(out)

"""
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
"""

#if __name__ == "__main__":
#    main()
    # This will run the main function when the script is executed directly
    # If this module is imported, the main function will not run automatically
    # This is a common practice to allow the module to be used both as a script and as an importable module.