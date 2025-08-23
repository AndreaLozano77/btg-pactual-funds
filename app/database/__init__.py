# /app/database/__init__.py
"""
Database package for BTG Pactual Funds API
Handles MongoDB connection and CRUD operations
"""

from .connection import (
    connect_to_mongo,
    close_mongo_connection,
    get_database,
    get_users_collection,
    get_funds_collection, 
    get_transactions_collection,
    mongodb
)

from .crud import (
    UserCRUD,
    FundCRUD,
    TransactionCRUD,
    serialize_document
)

__all__ = [
    # Connection functions
    "connect_to_mongo",
    "close_mongo_connection", 
    "get_database",
    "get_users_collection",
    "get_funds_collection",
    "get_transactions_collection",
    "mongodb",
    
    # CRUD classes
    "UserCRUD",
    "FundCRUD", 
    "TransactionCRUD",
    "serialize_document"
]

def get_user_balances_collection():
    """Get user balances collection"""
    return get_database().user_balances