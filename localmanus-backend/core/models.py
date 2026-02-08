from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime

class UserBase(SQLModel):
    username: str = Field(index=True, unique=True)
    email: Optional[str] = None
    full_name: Optional[str] = None

class User(UserBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    hashed_password: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

class UserCreate(UserBase):
    password: str

class UserRead(UserBase):
    id: int
    created_at: datetime

class Token(SQLModel):
    access_token: str
    token_type: str

class TokenData(SQLModel):
    username: Optional[str] = None

class UploadedFile(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    filename: str
    original_filename: str
    file_path: str
    file_size: int
    mime_type: Optional[str] = None
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)

class FileRead(SQLModel):
    id: int
    filename: str
    original_filename: str
    file_path: str
    file_size: int
    mime_type: Optional[str] = None
    uploaded_at: datetime

# Project Models
class Project(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    name: str
    description: Optional[str] = None
    color: str = Field(default="#3b82f6")  # Project theme color
    icon: str = Field(default="Folder")  # Lucide icon name
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class ProjectCreate(SQLModel):
    name: str
    description: Optional[str] = None
    color: Optional[str] = "#3b82f6"
    icon: Optional[str] = "Folder"

class ProjectUpdate(SQLModel):
    name: Optional[str] = None
    description: Optional[str] = None
    color: Optional[str] = None
    icon: Optional[str] = None

class ProjectRead(SQLModel):
    id: int
    user_id: int
    name: str
    description: Optional[str] = None
    color: str
    icon: str
    created_at: datetime
    updated_at: datetime
