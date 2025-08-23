# app/database/__init__.py
"""
Database package for BTG Pactual Funds API
Handles MongoDB connection and operations
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

__all__ = [
    "connect_to_mongo",
    "close_mongo_connection", 
    "get_database",
    "get_users_collection",
    "get_funds_collection",
    "get_transactions_collection",
    "mongodb"
]