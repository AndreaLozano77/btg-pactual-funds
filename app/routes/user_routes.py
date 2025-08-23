# routes/user_routes.py
from fastapi import APIRouter, HTTPException, status, Depends
from typing import List
from app.models.user import UserCreate, UserUpdate, UserResponse, UserLogin
from app.services.user_service import UserService
from app.utils.auth import get_current_user
import logging

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/users",
    tags=["Users"],
    responses={404: {"description": "Not found"}},
)


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(user_data: UserCreate):
    """
    Register a new user
    
    - **email**: Valid email address
    - **full_name**: User's full name
    - **phone**: Colombian phone number (+57)
    - **password**: Minimum 8 characters
    - **notification_preference**: email or sms
    """
    return await UserService.create_user(user_data)


@router.post("/login", response_model=dict)
async def login_user(credentials: UserLogin):
    """
    User login endpoint
    
    Returns access token for authenticated requests
    """
    user = await UserService.authenticate_user(credentials.email, credentials.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # TODO: Generate JWT token
    access_token = "fake-jwt-token-for-now"  # Replace with actual JWT generation
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user
    }


@router.get("/profile", response_model=UserResponse)
async def get_user_profile(current_user: UserResponse = Depends(get_current_user)):
    """
    Get current user profile
    
    Requires authentication
    """
    return current_user


@router.put("/profile", response_model=UserResponse)
async def update_user_profile(
    user_data: UserUpdate,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Update current user profile
    
    Requires authentication
    """
    return await UserService.update_user(current_user.id, user_data)


@router.get("/{user_id}", response_model=UserResponse)
async def get_user_by_id(user_id: str):
    """
    Get user by ID
    
    For administrative purposes
    """
    return await UserService.get_user_by_id(user_id)


@router.put("/{user_id}/balance", response_model=UserResponse)
async def update_user_balance(
    user_id: str,
    amount: int,
    operation: str = "add",
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Update user balance
    
    - **amount**: Amount to add or subtract
    - **operation**: "add" or "subtract"
    
    Requires authentication and admin privileges
    """
    # TODO: Add admin role check
    if current_user.role != "admin" and current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    return await UserService.update_user_balance(user_id, amount, operation)


@router.get("/{user_id}/funds", response_model=dict)
async def get_user_subscribed_funds(user_id: str):
    """
    Get user's subscribed funds
    
    Returns detailed information about user's fund subscriptions
    """
    user = await UserService.get_user_by_id(user_id)
    
    # TODO: Get detailed fund information from FundService
    return {
        "user_id": user_id,
        "subscribed_funds": user.subscribed_funds,
        "message": "Fund details integration pending"
    }