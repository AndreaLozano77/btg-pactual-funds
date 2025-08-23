# app/models/user_balance.py
from pydantic import BaseModel, Field
from typing import List, Optional

class UserBalance(BaseModel):
    user_id: str = Field(..., description="ID del usuario")
    current_balance: int = Field(..., description="Balance total (disponible + invertido)")
    available_balance: int = Field(..., description="Saldo disponible para invertir")
    subscribed_funds_value: int = Field(..., description="Valor total invertido en fondos")
    
    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "user123",
                "current_balance": 500000,
                "available_balance": 300000,
                "subscribed_funds_value": 200000
            }
        }

class SubscriptionRequest(BaseModel):
    fund_id: str = Field(..., description="ID del fondo al cual suscribirse")
    amount: int = Field(..., gt=0, description="Monto a invertir en COP")
    
    class Config:
        json_schema_extra = {
            "example": {
                "fund_id": "fund123",
                "amount": 100000
            }
        }

class CancellationRequest(BaseModel):
    fund_id: str = Field(..., description="ID del fondo a cancelar")
    
    class Config:
        json_schema_extra = {
            "example": {
                "fund_id": "fund123"
            }
        }