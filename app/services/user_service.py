# services/user_service.py
from typing import List, Optional
from fastapi import HTTPException, status
from app.models.user import User, UserCreate, UserUpdate, UserResponse
from app.database import UserCRUD
from app.utils.security import hash_password, verify_password
import logging

logger = logging.getLogger(__name__)


class UserService:
    """Service layer for user-related business logic"""
    
    @staticmethod
    async def create_user(user_data: UserCreate) -> UserResponse:
        """Create a new user with hashed password"""
        try:
            # Check if user already exists
            existing_user = await UserCRUD.get_user_by_email(user_data.email)
            if existing_user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already registered"
                )
            
            # Hash password
            hashed_password = hash_password(user_data.password)
            
            # Create user dict
            user_dict = user_data.dict(exclude={"password"})
            user_dict["hashed_password"] = hashed_password
            
            # Save to database
            created_user = await UserCRUD.create_user(user_dict)
            
            logger.info(f"User created successfully: {user_data.email}")
            return UserResponse(**created_user)
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error creating user: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error creating user"
            )
    
    @staticmethod
    async def get_user_by_id(user_id: str) -> UserResponse:
        """Get user by ID"""
        try:
            user = await UserCRUD.get_user_by_id(user_id)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
            return UserResponse(**user)
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting user by ID: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error retrieving user"
            )
    
    @staticmethod
    async def update_user(user_id: str, user_data: UserUpdate) -> UserResponse:
        """Update user information"""
        try:
            # Check if user exists
            existing_user = await UserCRUD.get_user_by_id(user_id)
            if not existing_user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
            
            # Update user
            updated_user = await UserCRUD.update_user(user_id, user_data.dict(exclude_unset=True))
            
            logger.info(f"User updated successfully: {user_id}")
            return UserResponse(**updated_user)
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error updating user: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error updating user"
            )
    
    @staticmethod
    async def authenticate_user(email: str, password: str) -> Optional[UserResponse]:
        """Authenticate user credentials"""
        try:
            user = await UserCRUD.get_user_by_email(email)
            if not user:
                return None
            
            if not verify_password(password, user.get("hashed_password")):
                return None
            
            if not user.get("is_active"):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Inactive user account"
                )
            
            return UserResponse(**user)
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error authenticating user: {e}")
            return None
    
    @staticmethod
    async def update_user_balance(user_id: str, amount: int, operation: str = "add") -> UserResponse:
        """Update user balance (add/subtract)"""
        try:
            user = await UserCRUD.get_user_by_id(user_id)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
            
            current_balance = user.get("balance", 0)
            
            if operation == "add":
                new_balance = current_balance + amount
            elif operation == "subtract":
                new_balance = current_balance - amount
                if new_balance < 0:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Insufficient balance"
                    )
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid operation"
                )
            
            updated_user = await UserCRUD.update_user(user_id, {"balance": new_balance})
            
            logger.info(f"User balance updated: {user_id} - {operation} {amount}")
            return UserResponse(**updated_user)
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error updating user balance: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error updating balance"
            )