from sqlalchemy import Column, Integer, String, LargeBinary, DateTime, Text
from sqlalchemy.types import TypeDecorator, CHAR
from sqlalchemy.dialects.postgresql import UUID
import uuid
import datetime
from .database import Base

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
                # hexstring
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
    password_hash = Column(String, nullable=False) # Argon2 hash of Master Password
    # We store the salt used for the Master Key derivation here.
    # When user provides MP, we combine with this salt to regenerate the MK for AES.
    master_key_salt = Column(LargeBinary, nullable=False) 

class PasswordEntry(Base):
    __tablename__ = "passwords"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    site_name = Column(String, index=True, nullable=False)
    username = Column(String, nullable=True)
    
    # Classification
    category = Column(String, nullable=False, default="General") # e.g. API Key, Web, App
    environment = Column(String, nullable=False, default="Production") # e.g. Prod, Dev, Local

    # Encrypted fields
    encrypted_password = Column(LargeBinary, nullable=False)
    nonce = Column(LargeBinary, nullable=False) # Needed for AES-GCM
    
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
