from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
from sqlalchemy_utils import ChoiceType
import uuid

Base = declarative_base()


class Users(Base):
    """ORM model for the Users table.
    This class defines the structure of the Users table in the database.
    """

    ROLE = (
        ('admin', 'Admin'),
        ('manager', 'Manager'),
        ('curator', 'Curator'),
        ('viewer', 'Viewer'),
    )
    __tablename__ = 'Users'
    
    user_id = Column(String(100), primary_key=True, nullable=False, unique=True, default=lambda: str(uuid.uuid4()))
    user_name = Column(String(100), nullable=False, unique=True)
    role = Column(ChoiceType(ROLE), nullable=False)
    email = Column(String(255), nullable=False, unique=True)
    password = Column(String(255), nullable=False)
    is_active = Column(Boolean, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)


    def __rep__(self):
        return f"Users(user_name={self.user_name}, role={self.role})"


class ActivityLog(Base):

    """Tracks actions performed by a user on various entities."""

    OPERATION = (
        ('create', 'Create'),
        ('update', 'Update'),
        ('delete', 'Delete'),
    )

    ROLE = (
        ('admin', 'Admin'),
        ('manager', 'Manager'),
        ('curator', 'Curator'),
        ('viewer', 'Viewer'),
    )

    __tablename__ = 'ActivityLog'

    id = Column(Integer, primary_key=True)
    user_name = Column(String(100), nullable=False)
    role = Column(ChoiceType(ROLE), nullable=False)
    entity_type = Column(String(100), nullable=False)  # e.g., "Test Case", "Target", "Domain"
    entity_id = Column(String(100), nullable=False)  # e.g., testcase_id, target_id
    note = Column(String(255), nullable=False)
    operation = Column(ChoiceType(OPERATION), nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    def __rep__(self):
        return f"ActivityLog(user_name={self.user_name}, entity_type={self.entity_type}, entity_id={self.entity_id}, operation={self.operation})"


