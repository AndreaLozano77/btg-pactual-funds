# app/services/user_service.py - BÁSICO PARA EMPEZAR
from fastapi import HTTPException, status
from app.models.user import User, UserCreate, UserUpdate, UserResponse
from app.database import get_database
from app.auth.security import hash_password, verify_password
from datetime import datetime
import uuid
import logging

logger = logging.getLogger(__name__)

class UserService:
    """Service layer for user-related business logic"""
    
    @staticmethod
    async def create_user(user_data: UserCreate) -> UserResponse:
        """Create a new user"""
        try:
            db = await get_database()
            
            # Check if user already exists
            existing_user = await db.users.find_one({"email": user_data.email})
            if existing_user:
                raise ValueError("User with this email already exists")
            
            # Hash password
            hashed_password = hash_password(user_data.password)
            
            # Create user document
            user_dict = user_data.dict(exclude={"password"})
            user_dict.update({
                "_id": str(uuid.uuid4()),
                "hashed_password": hashed_password,
                "balance": 500000,  # Initial balance
                "subscribed_funds": [],
                "role": "client",
                "is_active": True,
                "created_at": datetime.utcnow()
            })
            
            # Insert user
            result = await db.users.insert_one(user_dict)
            created_user = await db.users.find_one({"_id": result.inserted_id})
            
            # Return user response (without password)
            return UserResponse(**created_user)
            
        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Error creating user: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error creating user"
            )
    
    @staticmethod
    async def authenticate_user(email: str, password: str) -> UserResponse:
        """Authenticate user credentials"""
        try:
            db = await get_database()
            
            # Find user by email
            user = await db.users.find_one({"email": email})
            if not user:
                return None
            
            # Verify password
            if not verify_password(password, user["hashed_password"]):
                return None
            
            return UserResponse(**user)
            
        except Exception as e:
            logger.error(f"Error authenticating user: {e}")
            return None
    
    @staticmethod
    async def get_user_by_id(user_id: str) -> UserResponse:
        """Get user by ID"""
        try:
            db = await get_database()
            user = await db.users.find_one({"_id": user_id})
            
            if user:
                return UserResponse(**user)
            return None
            
        except Exception as e:
            logger.error(f"Error getting user by ID: {e}")
            return None
    
    @staticmethod
    async def update_user(user_id: str, user_data: UserUpdate) -> UserResponse:
        """Update user information"""
        try:
            db = await get_database()
            
            # Prepare update data
            update_data = {k: v for k, v in user_data.dict().items() if v is not None}
            update_data["updated_at"] = datetime.utcnow()
            
            # Update user
            result = await db.users.update_one(
                {"_id": user_id},
                {"$set": update_data}
            )
            
            if result.matched_count == 0:
                raise ValueError("User not found")
            
            # Return updated user
            updated_user = await db.users.find_one({"_id": user_id})
            return UserResponse(**updated_user)
            
        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Error updating user: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error updating user"
            )
    
    @staticmethod
    async def update_user_balance(user_id: str, amount: int, operation: str) -> UserResponse:
        """Update user balance"""
        try:
            db = await get_database()
            
            user = await db.users.find_one({"_id": user_id})
            if not user:
                raise ValueError("User not found")
            
            current_balance = user.get("balance", 0)
            
            if operation == "add":
                new_balance = current_balance + amount
            elif operation == "subtract":
                new_balance = current_balance - amount
                if new_balance < 0:
                    raise ValueError("Insufficient balance")
            else:
                raise ValueError("Invalid operation")
            
            # Update balance
            await db.users.update_one(
                {"_id": user_id},
                {"$set": {"balance": new_balance, "updated_at": datetime.utcnow()}}
            )
            
            # Return updated user
            updated_user = await db.users.find_one({"_id": user_id})
            return UserResponse(**updated_user)
            
        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Error updating user balance: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error updating balance"
            )
    
    @staticmethod
    async def get_all_users(skip: int = 0, limit: int = 100):
        """Get all users (admin function)"""
        try:
            db = await get_database()
            
            cursor = db.users.find().skip(skip).limit(limit)
            users = []
            async for user in cursor:
                users.append(UserResponse(**user))
            
            return users
            
        except Exception as e:
            logger.error(f"Error getting all users: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error retrieving users"
            )
    
    @staticmethod
    async def update_user_status(user_id: str, is_active: bool) -> UserResponse:
        """Update user active status"""
        try:
            db = await get_database()
            
            result = await db.users.update_one(
                {"_id": user_id},
                {"$set": {"is_active": is_active, "updated_at": datetime.utcnow()}}
            )
            
            if result.matched_count == 0:
                raise ValueError("User not found")
            
            updated_user = await db.users.find_one({"_id": user_id})
            return UserResponse(**updated_user)
            
        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Error updating user status: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error updating user status"
            )