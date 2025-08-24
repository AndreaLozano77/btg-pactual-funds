import os
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import ConnectionFailure
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class MongoDB:
    client: Optional[AsyncIOMotorClient] = None
    database = None

mongodb = MongoDB()

async def connect_to_mongo():
    """Create database connection"""
    try:
        # MongoDB connection string from environment variables
        mongodb_url = os.getenv(
            "MONGODB_URL", 
            "mongodb://localhost:27017"  # Default for local development
        )
        
        database_name = os.getenv("DATABASE_NAME", "btg_funds")
        
        logger.info(f"Connecting to MongoDB: {mongodb_url}")
        
        # Create client with connection options
        mongodb.client = AsyncIOMotorClient(
            mongodb_url,
            maxPoolSize=10,
            minPoolSize=1,
            maxIdleTimeMS=45000,
            serverSelectionTimeoutMS=10000,
            connectTimeoutMS=10000,
            socketTimeoutMS=20000,
        )
        
        # Select database
        mongodb.database = mongodb.client[database_name]
        
        # Test the connection
        await mongodb.client.admin.command('ping')
        logger.info("✅ Successfully connected to MongoDB")
        
        # Create indexes for better performance
        await create_indexes()
        
    except ConnectionFailure as e:
        logger.error(f"❌ Failed to connect to MongoDB: {e}")
        raise e
    except Exception as e:
        logger.error(f"❌ Unexpected error connecting to MongoDB: {e}")
        raise e

async def close_mongo_connection():
    """Close database connection"""
    if mongodb.client:
        mongodb.client.close()
        logger.info("✅ MongoDB connection closed")

async def create_indexes():
    """Create database indexes for better performance"""
    try:
        # Users collection indexes
        users_collection = mongodb.database.users
        await users_collection.create_index("email", unique=True)
        await users_collection.create_index("created_at")

        # User balances collection indexes
        user_balances_collection = mongodb.database.user_balances
        await user_balances_collection.create_index("user_id", unique=True)
        await user_balances_collection.create_index("last_updated")
                
        # Funds collection indexes  
        funds_collection = mongodb.database.funds
        await funds_collection.create_index("name", unique=True)
        await funds_collection.create_index("category")
        await funds_collection.create_index("is_active")
        
        # Transactions collection indexes
        transactions_collection = mongodb.database.transactions
        await transactions_collection.create_index("transaction_id", unique=True)
        await transactions_collection.create_index("user_id")
        await transactions_collection.create_index("fund_id") 
        await transactions_collection.create_index("created_at")
        await transactions_collection.create_index([("user_id", 1), ("created_at", -1)])
        
        logger.info("✅ Database indexes created successfully")
        
    except Exception as e:
        logger.warning(f"⚠️ Error creating indexes: {e}")

def get_database():
    """Get database instance"""
    if mongodb.database is None:  # SOLUCIÓN: Usar 'is None' en lugar de truthiness
        raise ConnectionError("Database not connected. Call connect_to_mongo() first.")
    return mongodb.database

# Collection helpers
def get_users_collection():
    """Get users collection"""
    return get_database().users

def get_funds_collection():
    """Get funds collection"""  
    return get_database().funds

def get_transactions_collection():
    """Get transactions collection"""
    return get_database().transactions