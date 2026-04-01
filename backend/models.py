# backend/models.py
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
from datetime import datetime, timezone
import uuid

class ProfileBase(BaseModel):
    name: str
    age: int
    city: str
    country: str = "Россия"
    descriptionShort: str
    descriptionFull: str
    images: List[str] = []
    height: int  # in cm
    weight: int  # in kg
    languages: List[str] = []
    tags: List[str] = []
    lat: float
    lng: float
    isActive: bool = True
    isFeatured: bool = False

class Profile(ProfileBase):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    slug: str
    distance: Optional[float] = None
    createdAt: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updatedAt: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class ProfileCreate(ProfileBase):
    pass

class ProfileUpdate(BaseModel):
    name: Optional[str] = None
    age: Optional[int] = None
    city: Optional[str] = None
    country: Optional[str] = None
    descriptionShort: Optional[str] = None
    descriptionFull: Optional[str] = None
    images: Optional[List[str]] = None
    height: Optional[int] = None
    weight: Optional[int] = None
    languages: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    lat: Optional[float] = None
    lng: Optional[float] = None
    isActive: Optional[bool] = None
    isFeatured: Optional[bool] = None

class AdminUser(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    username: str
    password_hash: str
    createdAt: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class AdminLogin(BaseModel):
    username: str
    password: str

class AdminLoginResponse(BaseModel):
    token: str
    username: str

class ContactMessage(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    email: str
    phone: str
    message: str
    createdAt: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class ContactMessageCreate(BaseModel):
    name: str
    email: str
    phone: str
    message: str