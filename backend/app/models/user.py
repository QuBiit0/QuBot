"""
User model - Authentication and user management
"""
from datetime import datetime
from typing import Optional, List
from uuid import UUID, uuid4
from sqlmodel import SQLModel, Field, Column, Relationship
from sqlalchemy import String, Boolean, DateTime, Integer
from enum import Enum


class UserRole(str, Enum):
    """User roles for access control"""
    ADMIN = "admin"
    USER = "user"
    VIEWER = "viewer"


class User(SQLModel, table=True):
    """User account for authentication"""
    __tablename__ = "user"
    
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    email: str = Field(
        sa_column=Column(String(255), unique=True, index=True, nullable=False)
    )
    username: str = Field(
        sa_column=Column(String(100), unique=True, index=True, nullable=False)
    )
    hashed_password: str = Field(sa_column=Column(String(255), nullable=False))
    
    # Profile
    full_name: Optional[str] = Field(default=None, sa_column=Column(String(200)))
    avatar_url: Optional[str] = Field(default=None, sa_column=Column(String(500)))
    
    # Role and permissions
    role: UserRole = Field(default=UserRole.USER, sa_column=Column(String(20)))
    is_active: bool = Field(default=True)
    is_verified: bool = Field(default=False)
    
    # Tracking
    last_login: Optional[datetime] = Field(default=None, sa_column=Column(DateTime))
    login_count: int = Field(default=0, sa_column=Column(Integer))
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # API key for programmatic access
    api_key: Optional[str] = Field(default=None, sa_column=Column(String(255), unique=True, index=True))
    api_key_created_at: Optional[datetime] = Field(default=None)
    
    # Relationships
    sessions: List["UserSession"] = Relationship(back_populates="user")


class UserSession(SQLModel, table=True):
    """Active user sessions for token revocation"""
    __tablename__ = "user_session"
    
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="user.id", index=True)
    token_jti: str = Field(sa_column=Column(String(255), unique=True, index=True))
    expires_at: datetime = Field(sa_column=Column(DateTime, nullable=False))
    created_at: datetime = Field(default_factory=datetime.utcnow)
    ip_address: Optional[str] = Field(default=None, sa_column=Column(String(45)))
    user_agent: Optional[str] = Field(default=None, sa_column=Column(String(500)))
    is_revoked: bool = Field(default=False)
    
    # Relationship
    user: User = Relationship(back_populates="sessions")


class UserCreate(SQLModel):
    """Schema for user registration"""
    email: str
    username: str
    password: str
    full_name: Optional[str] = None


class UserLogin(SQLModel):
    """Schema for user login"""
    email: str
    password: str


class UserResponse(SQLModel):
    """Schema for user response (safe to return)"""
    id: UUID
    email: str
    username: str
    full_name: Optional[str]
    role: UserRole
    is_active: bool
    avatar_url: Optional[str]
    created_at: datetime


class Token(SQLModel):
    """Schema for token response"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds


class TokenPayload(SQLModel):
    """Schema for JWT token payload"""
    sub: Optional[str] = None  # user_id
    exp: Optional[datetime] = None
    jti: Optional[str] = None  # token unique id
    type: Optional[str] = None  # access or refresh
    role: Optional[str] = None
