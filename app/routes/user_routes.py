# app/routes/user_routes.py - ACTUALIZADO CON JWT REAL
from fastapi import APIRouter, HTTPException, status, Depends
from typing import List
from app.models.user import UserCreate, UserUpdate, UserResponse, UserLogin
from app.services.user_service import UserService
from app.auth.security import get_current_user, get_current_admin_user
from app.auth.security import SecurityManager
import logging

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/users",
    tags=["User Management"],
    responses={404: {"description": "Not found"}},
)

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(user_data: UserCreate):
    """
    Register a new user
    
    - **email**: Valid email address (unique)
    - **full_name**: User's full name
    - **phone**: Colombian phone number (+57)
    - **password**: Minimum 8 characters
    - **notification_preference**: email or sms
    
    Returns the created user information (without password).
    """
    try:
        return await UserService.create_user(user_data)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error creating user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error creating user account"
        )

@router.post("/login", summary="User authentication")
async def login_user(credentials: UserLogin):
    """
    Authenticate user and return access token
    
    - **email**: User's email
    - **password**: User's password
    
    Returns:
    - **access_token**: JWT token for API authentication
    - **token_type**: Always "bearer"
    - **expires_in**: Token expiration time in seconds
    - **user**: Basic user information
    """
    try:
        # Authenticate user
        user = await UserService.authenticate_user(credentials.email, credentials.password)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is disabled"
            )
        
        # ✅ SOLUCIÓN: Crear token manualmente
        from datetime import datetime, timedelta
        from jose import jwt
        import os
        
        # Datos para el token
        token_data = {
            "sub": user.email,
            "id": user.id,
            "exp": datetime.utcnow() + timedelta(hours=24)
        }
        
        # Crear token (usa variable de entorno en producción)
        secret_key = os.getenv("JWT_SECRET_KEY", "temp-secret-key-for-development")
        access_token = jwt.encode(token_data, secret_key, algorithm="HS256")
        
        logger.info(f"User {user.email} logged in successfully")
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": 86400,  # 24 horas en segundos
            "user": {
                "id": user.id,
                "email": user.email,
                "full_name": user.full_name
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error during authentication"
        )

@router.get("/profile", response_model=UserResponse, summary="Get current user profile")
async def get_user_profile(current_user: UserResponse = Depends(get_current_user)):
    """
    Get current authenticated user's profile
    
    Requires valid JWT token in Authorization header:
    ```
    Authorization: Bearer <your-jwt-token>
    ```
    
    Returns complete user profile information.
    """
    return current_user

@router.put("/profile", response_model=UserResponse, summary="Update user profile")
async def update_user_profile(
    user_data: UserUpdate,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Update current authenticated user's profile
    
    - **phone**: New phone number (optional)
    - **full_name**: New full name (optional)
    - **notification_preference**: New notification preference (optional)
    
    Requires authentication. Users can only update their own profile.
    """
    try:
        return await UserService.update_user(current_user.id, user_data)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error updating user profile: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error updating profile"
        )

@router.get("/me/balance", summary="Get current user balance")
async def get_my_balance(current_user: UserResponse = Depends(get_current_user)):
    """
    Get current authenticated user's balance information
    
    Returns:
    - **balance**: Available balance in COP
    - **subscribed_funds**: List of subscribed fund IDs
    
    Requires authentication.
    """
    return {
        "user_id": current_user.id,
        "balance": current_user.balance,
        "subscribed_funds": current_user.subscribed_funds,
        "full_name": current_user.full_name,
        "email": current_user.email
    }

# ADMIN ENDPOINTS
@router.get("/", response_model=List[UserResponse], summary="Get all users (Admin only)")
async def get_all_users(
    current_admin: UserResponse = Depends(get_current_admin_user),
    skip: int = 0,
    limit: int = 100
):
    """
    Get all users in the system
    
    - **skip**: Number of users to skip (pagination)
    - **limit**: Maximum number of users to return
    
    Requires admin privileges.
    """
    try:
        return await UserService.get_all_users(skip=skip, limit=limit)
    except Exception as e:
        logger.error(f"Error getting all users: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving users"
        )

@router.get("/{user_id}", response_model=UserResponse, summary="Get user by ID (Admin only)")
async def get_user_by_id(
    user_id: str,
    current_admin: UserResponse = Depends(get_current_admin_user)
):
    """
    Get specific user by ID
    
    - **user_id**: Target user's ID
    
    Requires admin privileges.
    """
    user = await UserService.get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found"
        )
    return user

@router.put("/{user_id}/balance", response_model=UserResponse, summary="Update user balance (Admin only)")
async def update_user_balance(
    user_id: str,
    amount: int,
    operation: str = "add",  # "add" or "subtract"
    current_admin: UserResponse = Depends(get_current_admin_user)
):
    """
    Update user balance (Admin operation)
    
    - **user_id**: Target user's ID
    - **amount**: Amount to add or subtract
    - **operation**: "add" to increase balance, "subtract" to decrease
    
    Requires admin privileges.
    """
    if operation not in ["add", "subtract"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Operation must be 'add' or 'subtract'"
        )
    
    if amount < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Amount must be positive"
        )
    
    try:
        return await UserService.update_user_balance(user_id, amount, operation)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error updating user balance: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error updating balance"
        )

@router.put("/{user_id}/status", response_model=UserResponse, summary="Update user status (Admin only)")
async def update_user_status(
    user_id: str,
    is_active: bool,
    current_admin: UserResponse = Depends(get_current_admin_user)
):
    """
    Activate or deactivate user account
    
    - **user_id**: Target user's ID
    - **is_active**: True to activate, False to deactivate
    
    Requires admin privileges.
    """
    try:
        return await UserService.update_user_status(user_id, is_active)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error updating user status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error updating user status"
        )

@router.get("/{user_id}/funds", summary="Get user's subscribed funds (Admin only)")
async def get_user_subscribed_funds(
    user_id: str,
    current_admin: UserResponse = Depends(get_current_admin_user)
):
    """
    Get detailed information about user's fund subscriptions
    
    - **user_id**: Target user's ID
    
    Returns detailed fund subscription information.
    Requires admin privileges.
    """
    user = await UserService.get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found"
        )
    
    # TODO: Integrate with FundService to get detailed fund information
    return {
        "user_id": user_id,
        "user_name": user.full_name,
        "subscribed_funds": user.subscribed_funds,
        "balance": user.balance,
        "message": "Detailed fund information integration pending"
    }