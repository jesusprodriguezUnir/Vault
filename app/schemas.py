from pydantic import BaseModel
from typing import List, Optional
from uuid import UUID
from datetime import datetime

# --- Token / User ---
class UserCreate(BaseModel):
    username: str
    master_password: str

class UserResponse(BaseModel):
    id: int
    username: str
    class Config:
        from_attributes = True

# --- Categories ---
class CategoryBase(BaseModel):
    name: str
    description: Optional[str] = None

class CategoryCreate(CategoryBase):
    master_password: str # Required for auth

class CategoryUpdate(CategoryBase):
    master_password: str

class CategoryResponse(CategoryBase):
    id: UUID
    class Config:
        from_attributes = True

# --- Applications ---
class ApplicationBase(BaseModel):
    name: str
    description: Optional[str] = None
    category_id: UUID

class ApplicationCreate(ApplicationBase):
    master_password: str

class ApplicationUpdate(ApplicationBase):
    master_password: str

class DeleteRequest(BaseModel):
    master_password: str

class ApplicationResponse(ApplicationBase):
    id: UUID
    class Config:
        from_attributes = True

# --- Passwords ---
class PasswordEntryCreate(BaseModel):
    application_id: UUID
    username: Optional[str] = None
    environment: str = "Production"
    plaintext_password: str
    master_password: str 

class PasswordEntryResponse(BaseModel):
    id: UUID
    application_id: UUID
    username: Optional[str]
    environment: str
    created_at: datetime
    class Config:
        from_attributes = True

class PasswordEntryDecryptedResponse(PasswordEntryResponse):
    decrypted_password: str

# --- Hierarchy View ---
# Used to fetch full tree: Category -> Apps -> Passwords (metadata)
class ApplicationWithCount(ApplicationResponse):
    password_count: int

class CategoryWithApps(CategoryResponse):
    applications: List[ApplicationWithCount] = []
