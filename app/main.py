# main.py - VERSIÓN FUNCIONAL GARANTIZADA
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import uuid

app = FastAPI(
    title="BTG Pactual Funds API",
    description="API para gestión de fondos de inversión BTG Pactual",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# MODELOS BÁSICOS
class Fund(BaseModel):
    id: str
    name: str
    minimum_amount: int
    category: str
    is_active: bool = True

class Transaction(BaseModel):
    id: str
    transaction_id: str
    user_id: str
    fund_id: str
    fund_name: str
    transaction_type: str  # SUBSCRIPTION or CANCELLATION
    amount: int
    status: str = "COMPLETED"
    created_at: datetime

class UserBalance(BaseModel):
    user_id: str
    current_balance: int
    available_balance: int
    subscribed_funds_value: int

# DATOS DE PRUEBA
FUNDS_DB = [
    {
        "id": "fpv-btg-001",
        "name": "FPV_BTG_PACTUAL_RECAUDADORA",
        "minimum_amount": 75000,
        "category": "FPV",
        "is_active": True
    },
    {
        "id": "fic-btg-002", 
        "name": "FIC_BTG_PACTUAL_DINAMICA",
        "minimum_amount": 100000,
        "category": "FIC",
        "is_active": True
    },
    {
        "id": "fpv-btg-003",
        "name": "FPV_BTG_PACTUAL_ECOPETROL",
        "minimum_amount": 50000,
        "category": "FPV", 
        "is_active": True
    }
]

USERS_DB = {
    "user123": {
        "id": "user123",
        "email": "cliente@btgpactual.com",
        "balance": 500000,
        "subscribed_funds": []
    }
}

TRANSACTIONS_DB = []

# ENDPOINTS PRINCIPALES
@app.get("/")
async def root():
    return {
        "message": "BTG Pactual Funds API",
        "version": "1.0.0",
        "status": "active",
        "endpoints": {
            "docs": "/docs",
            "health": "/health",
            "funds": "/api/v1/funds",
            "subscribe": "/api/v1/funds/subscribe",
            "cancel": "/api/v1/funds/cancel",
            "history": "/api/v1/funds/user/history"
        }
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now()}

@app.get("/api/v1/funds", response_model=List[Fund])
async def get_all_funds():
    """Obtener todos los fondos disponibles"""
    return [Fund(**fund) for fund in FUNDS_DB]

@app.get("/api/v1/funds/{fund_id}", response_model=Fund)
async def get_fund(fund_id: str):
    """Obtener información de un fondo específico"""
    for fund in FUNDS_DB:
        if fund["id"] == fund_id:
            return Fund(**fund)
    raise HTTPException(status_code=404, detail="Fondo no encontrado")

@app.get("/api/v1/funds/user/balance")
async def get_user_balance(user_id: str = "user123"):
    """Obtener balance del usuario"""
    user = USERS_DB.get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    # Calcular valor invertido
    invested = 0
    for tx in TRANSACTIONS_DB:
        if tx["user_id"] == user_id and tx["status"] == "COMPLETED":
            if tx["transaction_type"] == "SUBSCRIPTION":
                invested += tx["amount"]
            elif tx["transaction_type"] == "CANCELLATION":
                invested -= tx["amount"]
    
    return UserBalance(
        user_id=user_id,
        current_balance=user["balance"] + invested,
        available_balance=user["balance"],
        subscribed_funds_value=invested
    )

@app.post("/api/v1/funds/subscribe")
async def subscribe_to_fund(fund_id: str, amount: int, user_id: str = "user123"):
    """Suscribirse a un fondo"""
    # Validar fondo
    fund = None
    for f in FUNDS_DB:
        if f["id"] == fund_id:
            fund = f
            break
    
    if not fund:
        raise HTTPException(status_code=404, detail="Fondo no encontrado")
    
    # Validar usuario
    user = USERS_DB.get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    # Validar monto mínimo
    if amount < fund["minimum_amount"]:
        raise HTTPException(
            status_code=400, 
            detail=f"Monto mínimo requerido: {fund['minimum_amount']}"
        )
    
    # Validar saldo
    if user["balance"] < amount:
        raise HTTPException(
            status_code=400,
            detail=f"No tiene saldo disponible para vincularse al fondo {fund['name']}"
        )
    
    # Crear transacción
    transaction = {
        "id": str(uuid.uuid4()),
        "transaction_id": str(uuid.uuid4()),
        "user_id": user_id,
        "fund_id": fund_id,
        "fund_name": fund["name"],
        "transaction_type": "SUBSCRIPTION",
        "amount": amount,
        "status": "COMPLETED",
        "created_at": datetime.now()
    }
    
    # Actualizar datos
    TRANSACTIONS_DB.append(transaction)
    USERS_DB[user_id]["balance"] -= amount
    USERS_DB[user_id]["subscribed_funds"].append(fund_id)
    
    return Transaction(**transaction)

@app.post("/api/v1/funds/cancel")
async def cancel_fund_subscription(fund_id: str, user_id: str = "user123"):
    """Cancelar suscripción a un fondo"""
    # Validar fondo
    fund = None
    for f in FUNDS_DB:
        if f["id"] == fund_id:
            fund = f
            break
    
    if not fund:
        raise HTTPException(status_code=404, detail="Fondo no encontrado")
    
    # Validar usuario
    user = USERS_DB.get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    # Verificar suscripción
    if fund_id not in user["subscribed_funds"]:
        raise HTTPException(
            status_code=400,
            detail="Usuario no está suscrito a este fondo"
        )
    
    # Calcular monto invertido
    invested_amount = 0
    for tx in TRANSACTIONS_DB:
        if (tx["user_id"] == user_id and tx["fund_id"] == fund_id and 
            tx["status"] == "COMPLETED"):
            if tx["transaction_type"] == "SUBSCRIPTION":
                invested_amount += tx["amount"]
            elif tx["transaction_type"] == "CANCELLATION":
                invested_amount -= tx["amount"]
    
    if invested_amount <= 0:
        raise HTTPException(
            status_code=400,
            detail="No hay inversión activa en este fondo"
        )
    
    # Crear transacción de cancelación
    transaction = {
        "id": str(uuid.uuid4()),
        "transaction_id": str(uuid.uuid4()),
        "user_id": user_id,
        "fund_id": fund_id,
        "fund_name": fund["name"],
        "transaction_type": "CANCELLATION",
        "amount": invested_amount,
        "status": "COMPLETED",
        "created_at": datetime.now()
    }
    
    # Actualizar datos
    TRANSACTIONS_DB.append(transaction)
    USERS_DB[user_id]["balance"] += invested_amount
    USERS_DB[user_id]["subscribed_funds"].remove(fund_id)
    
    return Transaction(**transaction)

@app.get("/api/v1/funds/user/history")
async def get_user_transaction_history(user_id: str = "user123"):
    """Obtener historial de transacciones del usuario"""
    user_transactions = [
        tx for tx in TRANSACTIONS_DB 
        if tx["user_id"] == user_id
    ]
    
    # Calcular estadísticas
    total_invested = 0
    for tx in user_transactions:
        if tx["status"] == "COMPLETED":
            if tx["transaction_type"] == "SUBSCRIPTION":
                total_invested += tx["amount"]
            elif tx["transaction_type"] == "CANCELLATION":
                total_invested -= tx["amount"]
    
    user = USERS_DB.get(user_id, {"balance": 0})
    
    return {
        "transactions": [Transaction(**tx) for tx in user_transactions],
        "total_invested": max(0, total_invested),
        "available_balance": user["balance"],
        "total_transactions": len(user_transactions)
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)