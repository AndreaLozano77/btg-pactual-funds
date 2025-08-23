# app/routes/fund_routes.py
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer
from app.services.fund_service import FundService
from app.models.fund import Fund, FundCreate
from app.models.transaction import Transaction, TransactionHistory
from app.models.user_balance import UserBalance, SubscriptionRequest, CancellationRequest
from app.database import get_database
from typing import List

router = APIRouter(prefix="/api/v1/funds", tags=["funds"])
security = HTTPBearer()

def get_fund_service():
    return FundService()

def get_current_user_id(token: str = Depends(security)) -> str:
    # Por ahora simulamos la extracción del user_id del token
    # En implementación real decodificarías el JWT
    return "user123"  # Usuario de prueba

@router.get("/", response_model=List[Fund])
async def get_all_funds(
    fund_service: FundService = Depends(get_fund_service)
):
    """Obtener todos los fondos disponibles"""
    try:
        return await fund_service.get_all_funds()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener fondos: {str(e)}"
        )

@router.get("/{fund_id}", response_model=Fund)
async def get_fund(
    fund_id: str,
    fund_service: FundService = Depends(get_fund_service)
):
    """Obtener información de un fondo específico"""
    fund = await fund_service.get_fund_by_id(fund_id)
    if not fund:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Fondo no encontrado"
        )
    return fund

@router.post("/", response_model=Fund)
async def create_fund(
    fund_data: FundCreate,
    fund_service: FundService = Depends(get_fund_service)
):
    """Crear un nuevo fondo (solo para administradores)"""
    try:
        return await fund_service.create_fund(fund_data)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al crear fondo: {str(e)}"
        )

@router.get("/user/balance", response_model=UserBalance)
async def get_user_balance(
    user_id: str = Depends(get_current_user_id),
    fund_service: FundService = Depends(get_fund_service)
):
    """Obtener balance y portafolio del usuario"""
    try:
        return await fund_service.get_user_balance(user_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener balance: {str(e)}"
        )

@router.post("/subscribe", response_model=Transaction)
async def subscribe_to_fund(
    subscription: SubscriptionRequest,
    user_id: str = Depends(get_current_user_id),
    fund_service: FundService = Depends(get_fund_service)
):
    """Suscribirse a un fondo"""
    try:
        return await fund_service.subscribe_to_fund(user_id, subscription)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error en suscripción: {str(e)}"
        )

@router.post("/cancel", response_model=Transaction)
async def cancel_fund_subscription(
    cancellation: CancellationRequest,
    user_id: str = Depends(get_current_user_id),
    fund_service: FundService = Depends(get_fund_service)
):
    """Cancelar suscripción a un fondo"""
    try:
        return await fund_service.cancel_fund_subscription(user_id, cancellation)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error en cancelación: {str(e)}"
        )

@router.get("/user/history", response_model=TransactionHistory)
async def get_user_transaction_history(
    user_id: str = Depends(get_current_user_id),
    fund_service: FundService = Depends(get_fund_service)
):
    """Obtener historial de transacciones del usuario"""
    try:
        return await fund_service.get_user_transaction_history(user_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener historial: {str(e)}"
        )