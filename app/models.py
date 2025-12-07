from sqlalchemy import Column, Integer, String, LargeBinary, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.types import TypeDecorator, CHAR
from sqlalchemy.dialects.postgresql import UUID
import uuid
import datetime
from .database import Base

# --- GUID Type for SQLite/Postgres Compatibility ---
class GUID(TypeDecorator):
    """Platform-independent GUID type.
    Uses PostgreSQL's UUID type, otherwise uses
    CHAR(32), storing as stringified hex values.
    """
    impl = CHAR
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(UUID())
        else:
            return dialect.type_descriptor(CHAR(32))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        elif dialect.name == 'postgresql':
            return str(value)
        else:
            if not isinstance(value, uuid.UUID):
                return "%.32x" % uuid.UUID(value).int
            else:
                return "%.32x" % value.int

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        else:
            if not isinstance(value, uuid.UUID):
                return uuid.UUID(value)
            else:
                return value

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False) 
    master_key_salt = Column(LargeBinary, nullable=False) 

class Category(Base):
    __tablename__ = "categories"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    name = Column(String, unique=True, index=True, nullable=False)
    description = Column(String, nullable=True)
    
    # Relationship
    applications = relationship("Application", back_populates="category", cascade="all, delete-orphan")

class Application(Base):
    __tablename__ = "applications"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    name = Column(String, index=True, nullable=False)
    description = Column(String, nullable=True)
    category_id = Column(GUID(), ForeignKey("categories.id"), nullable=False)

    # Relationships
    category = relationship("Category", back_populates="applications")
    passwords = relationship("PasswordEntry", back_populates="application", cascade="all, delete-orphan")

class PasswordEntry(Base):
    __tablename__ = "passwords"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    application_id = Column(GUID(), ForeignKey("applications.id"), nullable=False)
    
    username = Column(String, nullable=True)
    environment = Column(String, nullable=False, default="Production")

    # Encrypted fields
    encrypted_password = Column(LargeBinary, nullable=False)
    nonce = Column(LargeBinary, nullable=False) 
    
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # Relationship
    application = relationship("Application", back_populates="passwords")
