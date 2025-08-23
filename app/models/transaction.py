# app/models/transaction.py
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum
import uuid

class TransactionType(str, Enum):
    SUBSCRIPTION = "SUBSCRIPTION"    # Suscripción/Apertura
    CANCELLATION = "CANCELLATION"   # Cancelación

class TransactionStatus(str, Enum):
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    PENDING = "PENDING"

class Transaction(BaseModel):
    id: Optional[str] = Field(None, alias="_id")
    transaction_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="ID único de transacción")
    user_id: str = Field(..., description="ID del usuario")
    fund_id: str = Field(..., description="ID del fondo")
    fund_name: str = Field(..., description="Nombre del fondo")
    transaction_type: TransactionType = Field(..., description="Tipo de transacción")
    amount: int = Field(..., description="Monto de la transacción en COP")
    status: TransactionStatus = Field(default=TransactionStatus.COMPLETED)
    created_at: datetime = Field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    
    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "user_id": "user123",
                "fund_id": "fund456",
                "fund_name": "FPV_BTG_PACTUAL_RECAUDADORA",
                "transaction_type": "SUBSCRIPTION",
                "amount": 100000,
                "status": "COMPLETED"
            }
        }

class TransactionCreate(BaseModel):
    user_id: str
    fund_id: str
    transaction_type: TransactionType
    amount: int

class TransactionHistory(BaseModel):
    transactions: list[Transaction]
    total_invested: int = Field(description="Total invertido actualmente")
    available_balance: int = Field(description="Saldo disponible")
    total_transactions: int = Field(description="Número total de transacciones")