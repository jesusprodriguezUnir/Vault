from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from uuid import UUID

# Shared properties
class PasswordEntryBase(BaseModel):
    site_name: str
    username: Optional[str] = None
    category: str = "General"
    environment: str = "Production"

# Properties to receive on creation
class PasswordEntryCreate(PasswordEntryBase):
    plaintext_password: str
    master_password: str # Required to derive the key for encryption

# Properties to receive for decryption request
class PasswordEntryDecryptRequest(BaseModel):
    entry_id: UUID
    master_password: str

# Properties to return to client (Metadata only)
class PasswordEntryResponse(PasswordEntryBase):
    id: UUID
    created_at: datetime
    
    class Config:
        from_attributes = True

# Response with decrypted password
class PasswordEntryDecryptedResponse(PasswordEntryResponse):
    decrypted_password: str

# User setup
class UserCreate(BaseModel):
    username: str
    master_password: str
