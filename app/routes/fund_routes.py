# app/routes/fund_routes.py
from fastapi import APIRouter, HTTPException, status, Depends, Query
from typing import List, Optional
from app.models.fund import Fund, FundCreate, FundUpdate
from app.models.transaction import Transaction, TransactionHistory
from app.models.user_balance import UserBalance, SubscriptionRequest, CancellationRequest
from app.services.fund_service import FundService
from app.auth.security import get_current_user
from app.models.user import UserResponse
import logging

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/funds",
    tags=["Funds Management"],
    responses={
        404: {"description": "Resource not found"},
        400: {"description": "Bad request"},
        401: {"description": "Unauthorized"},
        500: {"description": "Internal server error"}
    },
)

# Initialize service
fund_service = FundService()

@router.get("/", response_model=List[Fund], summary="Get all available funds")
async def get_all_funds(
    category: Optional[str] = Query(None, description="Filter by fund category (FPV, FIC)"),
    is_active: Optional[bool] = Query(True, description="Filter by active status"),
    min_amount: Optional[int] = Query(None, description="Filter by minimum amount")
):
    """
    Retrieve all available investment funds.
    
    - **category**: Filter by fund category (FPV, FIC)
    - **is_active**: Include only active funds (default: True)
    - **min_amount**: Filter funds with minimum amount less than or equal to this value
    
    Returns list of available funds matching the criteria.
    """
    try:
        funds = await fund_service.get_all_funds()
        
        # Apply filters
        if category:
            funds = [f for f in funds if f.category.value == category.upper()]
        if is_active is not None:
            funds = [f for f in funds if f.is_active == is_active]
        if min_amount is not None:
            funds = [f for f in funds if f.minimum_amount <= min_amount]
            
        return funds
    except Exception as e:
        logger.error(f"Error retrieving funds: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving funds"
        )

@router.get("/{fund_id}", response_model=Fund, summary="Get fund by ID")
async def get_fund_by_id(fund_id: str):
    """
    Get detailed information about a specific fund.
    
    - **fund_id**: Unique identifier of the fund
    
    Returns detailed fund information.
    """
    fund = await fund_service.get_fund_by_id(fund_id)
    if not fund:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Fund with ID {fund_id} not found"
        )
    return fund

@router.post("/", response_model=Fund, summary="Create new fund", status_code=status.HTTP_201_CREATED)
async def create_fund(
    fund_data: FundCreate,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Create a new investment fund.
    
    - **name**: Fund name (must be unique)
    - **minimum_amount**: Minimum investment amount in COP
    - **category**: Fund category (FPV or FIC)
    
    Requires admin privileges.
    """
    # TODO: Add admin role check
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can create funds"
        )
    
    return await fund_service.create_fund(fund_data)

@router.get("/user/balance", response_model=UserBalance, summary="Get user balance and portfolio")
async def get_user_balance(current_user: UserResponse = Depends(get_current_user)):
    """
    Get current user's balance and investment portfolio.
    
    Returns:
    - **current_balance**: Total balance (available + invested)
    - **available_balance**: Available cash for new investments
    - **subscribed_funds_value**: Total amount invested in funds
    
    Requires authentication.
    """
    return await fund_service.get_user_balance(current_user.id)

@router.post("/subscribe", response_model=Transaction, summary="Subscribe to a fund")
async def subscribe_to_fund(
    subscription_request: SubscriptionRequest,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Subscribe to an investment fund.
    
    - **fund_id**: ID of the fund to subscribe to
    - **amount**: Investment amount in COP
    
    Validations:
    - Fund must exist and be active
    - Amount must meet minimum investment requirement
    - User must have sufficient available balance
    
    Returns transaction details upon successful subscription.
    """
    try:
        return await fund_service.subscribe_to_fund(current_user.id, subscription_request)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error in fund subscription: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error processing subscription"
        )

@router.post("/cancel", response_model=Transaction, summary="Cancel fund subscription")
async def cancel_fund_subscription(
    cancellation_request: CancellationRequest,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Cancel subscription to an investment fund.
    
    - **fund_id**: ID of the fund to cancel subscription
    
    Validations:
    - User must be currently subscribed to the fund
    - Must have active investment in the fund
    
    Returns transaction details and refunds the invested amount.
    """
    try:
        return await fund_service.cancel_fund_subscription(current_user.id, cancellation_request)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error in fund cancellation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error processing cancellation"
        )

@router.get("/user/history", response_model=TransactionHistory, summary="Get user transaction history")
async def get_user_transaction_history(
    current_user: UserResponse = Depends(get_current_user),
    limit: Optional[int] = Query(50, description="Maximum number of transactions to return", ge=1, le=100),
    offset: Optional[int] = Query(0, description="Number of transactions to skip", ge=0)
):
    """
    Get user's complete transaction history.
    
    - **limit**: Maximum number of transactions to return (1-100, default: 50)
    - **offset**: Number of transactions to skip for pagination (default: 0)
    
    Returns:
    - **transactions**: List of user transactions (newest first)
    - **total_invested**: Current total investment amount
    - **available_balance**: Available cash balance
    - **total_transactions**: Total number of transactions
    
    Requires authentication.
    """
    return await fund_service.get_user_transaction_history(current_user.id)

@router.get("/user/portfolio", summary="Get user investment portfolio summary")
async def get_user_portfolio(current_user: UserResponse = Depends(get_current_user)):
    """
    Get detailed portfolio breakdown by fund.
    
    Returns investment summary grouped by fund with performance metrics.
    
    Requires authentication.
    """
    # TODO: Implement portfolio breakdown
    return {
        "user_id": current_user.id,
        "message": "Portfolio breakdown feature coming soon",
        "balance": await fund_service.get_user_balance(current_user.id)
    }