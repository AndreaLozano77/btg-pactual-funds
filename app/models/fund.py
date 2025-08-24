# app/models/fund.py
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum

class FundCategory(str, Enum):
    FPV = "FPV"  # Fondo de Pensiones Voluntarias
    FIC = "FIC"  # Fondo de Inversión Colectiva

class Fund(BaseModel):
    id: Optional[str] = Field(None, alias="_id")
    name: str = Field(..., description="Nombre del fondo")
    minimum_amount: int = Field(..., description="Monto mínimo de vinculación en COP")
    category: FundCategory = Field(..., description="Categoría del fondo")
    is_active: bool = Field(True, description="Si el fondo está activo")
    created_at: datetime = Field(default_factory=datetime.now)
    
    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "name": "FPV_BTG_PACTUAL_RECAUDADORA",
                "minimum_amount": 75000,
                "category": "FPV",
                "is_active": True
            }
        }

class FundCreate(BaseModel):
    name: str
    minimum_amount: int
    category: FundCategory
    
class FundUpdate(BaseModel):
    name: Optional[str] = None
    minimum_amount: Optional[int] = None
    category: Optional[FundCategory] = None
    is_active: Optional[bool] = None