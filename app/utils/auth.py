# app/utils/auth.py
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.utils.security import verify_token
from app.services.user_service import UserService
from app.models.user import UserResponse
import logging

logger = logging.getLogger(__name__)

# Security scheme
security = HTTPBearer()


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> UserResponse:
    """
    Get current user from JWT token
    
    This function validates the JWT token and returns the current user
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Extract token from credentials
        token = credentials.credentials
        
        # Verify token and get user_id
        user_id = verify_token(token)
        if user_id is None:
            raise credentials_exception
            
        # Get user from database
        user = await UserService.get_user_by_id(user_id)
        if user is None:
            raise credentials_exception
            
        return user
        
    except HTTPException:
        raise credentials_exception
    except Exception as e:
        logger.error(f"Error getting current user: {e}")
        raise credentials_exception


async def get_current_active_user(current_user: UserResponse = Depends(get_current_user)) -> UserResponse:
    """
    Get current active user
    
    Ensures the user account is active
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Inactive user"
        )
    return current_user


async def get_current_admin_user(current_user: UserResponse = Depends(get_current_user)) -> UserResponse:
    """
    Get current admin user
    
    Ensures the user has admin privileges
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_user


# Optional: Simple dependency for endpoints that don't require authentication
async def get_current_user_optional(credentials: HTTPAuthorizationCredentials = Depends(security)) -> UserResponse:
    """
    Get current user (optional authentication)
    
    Returns None if no valid token provided, otherwise returns user
    """
    if not credentials:
        return None
    
    try:
        token = credentials.credentials
        user_id = verify_token(token)
        if user_id is None:
            return None
        
        user = await UserService.get_user_by_id(user_id)
        return user
    except Exception:
        return None