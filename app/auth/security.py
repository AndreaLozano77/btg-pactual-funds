# app/auth/security.py
from datetime import datetime, timedelta
from typing import Optional, Union
import os
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from passlib.context import CryptContext
from jose import JWTError, jwt
from app.models.user import UserResponse
import logging

logger = logging.getLogger(__name__)

# Configuration
JWT_SECRET = os.getenv("JWT_SECRET", "btg-pactual-super-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# HTTP Bearer token scheme
security = HTTPBearer()

class SecurityManager:
    """Centralized security management"""
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        return pwd_context.verify(plain_password, hashed_password)
    
    @staticmethod
    def get_password_hash(password: str) -> str:
        """Hash a password"""
        return pwd_context.hash(password)
    
    @staticmethod
    def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """
        Create a JWT access token
        
        Args:
            data: Data to encode in the token (usually user info)
            expires_delta: Custom expiration time
            
        Returns:
            Encoded JWT token
        """
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "access"
        })
        
        encoded_jwt = jwt.encode(to_encode, JWT_SECRET, algorithm=ALGORITHM)
        return encoded_jwt
    
    @staticmethod
    def verify_token(token: str) -> Optional[dict]:
        """
        Verify and decode a JWT token
        
        Args:
            token: JWT token to verify
            
        Returns:
            Decoded token payload or None if invalid
        """
        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=[ALGORITHM])
            
            # Check if token is expired
            exp = payload.get("exp")
            if exp is None:
                return None
                
            if datetime.utcnow() > datetime.fromtimestamp(exp):
                return None
                
            return payload
            
        except JWTError as e:
            logger.warning(f"JWT verification failed: {e}")
            return None
    
    @staticmethod
    def create_user_token(user: UserResponse) -> dict:
        """
        Create a complete token response for a user
        
        Args:
            user: User object
            
        Returns:
            Token response with access token and user info
        """
        # Token payload
        token_data = {
            "sub": user.email,  # Subject (user identifier)
            "user_id": user.id,
            "email": user.email,
            "role": user.role,
            "full_name": user.full_name
        }
        
        # Create token
        access_token = SecurityManager.create_access_token(data=token_data)
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,  # seconds
            "user": {
                "id": user.id,
                "email": user.email,
                "full_name": user.full_name,
                "role": user.role,
                "balance": user.balance
            }
        }

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> UserResponse:
    """
    Dependency to get current authenticated user from JWT token
    
    Args:
        credentials: HTTP Authorization credentials from request header
        
    Returns:
        Current authenticated user
        
    Raises:
        HTTPException: If token is invalid or user not found
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Extract token from credentials
        token = credentials.credentials
        
        # Verify token
        payload = SecurityManager.verify_token(token)
        if payload is None:
            logger.warning("Invalid token received")
            raise credentials_exception
        
        # Extract user info
        email: str = payload.get("sub")
        user_id: str = payload.get("user_id")
        
        if email is None or user_id is None:
            logger.warning("Token missing required fields")
            raise credentials_exception
            
    except Exception as e:
        logger.error(f"Error processing token: {e}")
        raise credentials_exception
    
    # Get user from database
    try:
        from app.services.user_service import UserService  # Import local
        user = await UserService.get_user_by_id(user_id)
        if user is None:
            logger.warning(f"User {user_id} not found in database")
            raise credentials_exception
            
        return user
        
    except Exception as e:
        logger.error(f"Error fetching user from database: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error validating user"
        )

async def get_current_admin_user(current_user: UserResponse = Depends(get_current_user)) -> UserResponse:
    """
    Dependency to get current authenticated admin user
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        Current authenticated admin user
        
    Raises:
        HTTPException: If user doesn't have admin privileges
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    return current_user

def create_test_token(user_id: str, email: str, role: str = "client") -> str:
    """
    Create a test token for development/testing purposes
    
    Args:
        user_id: User ID
        email: User email
        role: User role
        
    Returns:
        JWT token
    """
    token_data = {
        "sub": email,
        "user_id": user_id,
        "email": email,
        "role": role,
        "full_name": "Test User"
    }
    
    return SecurityManager.create_access_token(data=token_data)

# Utility functions for password management
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Wrapper for password verification"""
    return SecurityManager.verify_password(plain_password, hashed_password)

def hash_password(password: str) -> str:
    """Wrapper for password hashing"""
    return SecurityManager.get_password_hash(password)