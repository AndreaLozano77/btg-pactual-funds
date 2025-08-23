from pydantic import BaseModel, Field, EmailStr, validator
from typing import Optional, List
from datetime import datetime
from enum import Enum


class NotificationPreference(str, Enum):
    EMAIL = "email"
    SMS = "sms"


class UserRole(str, Enum):
    ADMIN = "admin"
    CLIENT = "client"


class User(BaseModel):
    id: Optional[str] = Field(None, alias="_id")
    email: EmailStr = Field(..., description="Email del usuario")
    phone: Optional[str] = Field(None, description="Número de teléfono para SMS")
    full_name: str = Field(..., min_length=2, max_length=100, description="Nombre completo")
    balance: int = Field(default=500000, ge=0, description="Saldo disponible en COP")
    notification_preference: NotificationPreference = Field(default=NotificationPreference.EMAIL)
    subscribed_funds: List[str] = Field(default_factory=list, description="IDs de fondos suscritos")
    role: UserRole = Field(default=UserRole.CLIENT)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None

    @validator('phone')
    def validate_phone(cls, v):
        if v and not v.startswith('+57'):
            raise ValueError('Número de teléfono debe tener formato colombiano (+57)')
        return v

    class Config:
        allow_population_by_field_name = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
        schema_extra = {
            "example": {
                "email": "cliente@btgpactual.com",
                "phone": "+573001234567",
                "full_name": "Juan Pérez",
                "balance": 500000,
                "notification_preference": "email"
            }
        }


class UserCreate(BaseModel):
    email: EmailStr
    phone: Optional[str] = None
    full_name: str = Field(..., min_length=2, max_length=100)
    notification_preference: NotificationPreference = NotificationPreference.EMAIL
    password: str = Field(..., min_length=8, description="Contraseña mínimo 8 caracteres")

    @validator('phone')
    def validate_phone(cls, v):
        if v and not v.startswith('+57'):
            raise ValueError('Número de teléfono debe tener formato colombiano (+57)')
        return v


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserUpdate(BaseModel):
    phone: Optional[str] = None
    full_name: Optional[str] = Field(None, min_length=2, max_length=100)
    notification_preference: Optional[NotificationPreference] = None
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    @validator('phone')
    def validate_phone(cls, v):
        if v and not v.startswith('+57'):
            raise ValueError('Número de teléfono debe tener formato colombiano (+57)')
        return v


class UserResponse(BaseModel):
    id: str
    email: str
    phone: Optional[str]
    full_name: str
    balance: int
    notification_preference: str
    subscribed_funds: List[str]
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class UserBalance(BaseModel):
    user_id: str
    current_balance: int
    available_balance: int
    subscribed_funds_value: int