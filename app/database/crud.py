from typing import List, Optional, Dict, Any
from bson import ObjectId
from pymongo.errors import DuplicateKeyError
import logging

from .connection import get_users_collection, get_funds_collection, get_transactions_collection
from ..models import (
    User, UserCreate, UserUpdate,
    Fund, FundCreate, FundUpdate, 
    Transaction, TransactionCreate
)

logger = logging.getLogger(__name__)

# Helper function to convert ObjectId to string
def serialize_document(doc: Dict[Any, Any]) -> Dict[Any, Any]:
    """Convert MongoDB ObjectId to string for JSON serialization"""
    if doc and "_id" in doc:
        doc["_id"] = str(doc["_id"])
    return doc

# User CRUD Operations
class UserCRUD:
    
    @staticmethod
    async def create_user(user: UserCreate, hashed_password: str) -> User:
        """Create a new user"""
        users_collection = get_users_collection()
        
        user_dict = user.dict()
        user_dict["password"] = hashed_password  # Store hashed password
        user_dict.pop("password", None)  # Remove plain password from UserCreate
        
        try:
            result = await users_collection.insert_one(user_dict)
            created_user = await users_collection.find_one({"_id": result.inserted_id})
            return User(**serialize_document(created_user))
        except DuplicateKeyError:
            raise ValueError("Email already registered")
    
    @staticmethod
    async def get_user_by_id(user_id: str) -> Optional[User]:
        """Get user by ID"""
        users_collection = get_users_collection()
        user_doc = await users_collection.find_one({"_id": ObjectId(user_id)})
        return User(**serialize_document(user_doc)) if user_doc else None
    
    @staticmethod
    async def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
        """Get user by email (includes password for authentication)"""
        users_collection = get_users_collection()
        user_doc = await users_collection.find_one({"email": email})
        return serialize_document(user_doc) if user_doc else None
    
    @staticmethod
    async def update_user_balance(user_id: str, new_balance: int) -> bool:
        """Update user balance"""
        users_collection = get_users_collection()
        result = await users_collection.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": {"balance": new_balance}}
        )
        return result.modified_count > 0
    
    @staticmethod
    async def add_fund_subscription(user_id: str, fund_id: str) -> bool:
        """Add fund to user's subscribed funds"""
        users_collection = get_users_collection()
        result = await users_collection.update_one(
            {"_id": ObjectId(user_id)},
            {"$addToSet": {"subscribed_funds": fund_id}}
        )
        return result.modified_count > 0
    
    @staticmethod
    async def remove_fund_subscription(user_id: str, fund_id: str) -> bool:
        """Remove fund from user's subscribed funds"""
        users_collection = get_users_collection()
        result = await users_collection.update_one(
            {"_id": ObjectId(user_id)},
            {"$pull": {"subscribed_funds": fund_id}}
        )
        return result.modified_count > 0

# Fund CRUD Operations
class FundCRUD:
    
    @staticmethod
    async def create_fund(fund: FundCreate) -> Fund:
        """Create a new fund"""
        funds_collection = get_funds_collection()
        
        fund_dict = fund.dict()
        try:
            result = await funds_collection.insert_one(fund_dict)
            created_fund = await funds_collection.find_one({"_id": result.inserted_id})
            return Fund(**serialize_document(created_fund))
        except DuplicateKeyError:
            raise ValueError("Fund name already exists")
    
    @staticmethod
    async def get_fund_by_id(fund_id: str) -> Optional[Fund]:
        """Get fund by ID"""
        funds_collection = get_funds_collection()
        fund_doc = await funds_collection.find_one({"_id": ObjectId(fund_id)})
        return Fund(**serialize_document(fund_doc)) if fund_doc else None
    
    @staticmethod
    async def get_all_funds(active_only: bool = True) -> List[Fund]:
        """Get all funds"""
        funds_collection = get_funds_collection()
        query = {"is_active": True} if active_only else {}
        
        cursor = funds_collection.find(query).sort("name", 1)
        funds = []
        async for fund_doc in cursor:
            funds.append(Fund(**serialize_document(fund_doc)))
        return funds
    
    @staticmethod
    async def get_funds_by_category(category: str) -> List[Fund]:
        """Get funds by category"""
        funds_collection = get_funds_collection()
        cursor = funds_collection.find({"category": category, "is_active": True})
        
        funds = []
        async for fund_doc in cursor:
            funds.append(Fund(**serialize_document(fund_doc)))
        return funds

# Transaction CRUD Operations  
class TransactionCRUD:
    
    @staticmethod
    async def create_transaction(transaction: Transaction) -> Transaction:
        """Create a new transaction"""
        transactions_collection = get_transactions_collection()
        
        transaction_dict = transaction.dict(exclude={"id"})
        result = await transactions_collection.insert_one(transaction_dict)
        
        created_transaction = await transactions_collection.find_one({"_id": result.inserted_id})
        return Transaction(**serialize_document(created_transaction))
    
    @staticmethod
    async def get_transaction_by_id(transaction_id: str) -> Optional[Transaction]:
        """Get transaction by ID"""
        transactions_collection = get_transactions_collection()
        transaction_doc = await transactions_collection.find_one({"transaction_id": transaction_id})
        return Transaction(**serialize_document(transaction_doc)) if transaction_doc else None
    
    @staticmethod
    async def get_user_transactions(
        user_id: str, 
        limit: int = 50, 
        skip: int = 0
    ) -> List[Transaction]:
        """Get user transaction history"""
        transactions_collection = get_transactions_collection()
        
        cursor = transactions_collection.find(
            {"user_id": user_id}
        ).sort("created_at", -1).skip(skip).limit(limit)
        
        transactions = []
        async for transaction_doc in cursor:
            transactions.append(Transaction(**serialize_document(transaction_doc)))
        return transactions
    
    @staticmethod
    async def update_transaction_status(
        transaction_id: str, 
        status: str, 
        error_message: Optional[str] = None
    ) -> bool:
        """Update transaction status"""
        transactions_collection = get_transactions_collection()
        
        update_data = {"status": status}
        if error_message:
            update_data["error_message"] = error_message
        if status == "completed":
            from datetime import datetime
            update_data["completed_at"] = datetime.utcnow()
        
        result = await transactions_collection.update_one(
            {"transaction_id": transaction_id},
            {"$set": update_data}
        )
        return result.modified_count > 0