"""
Seed data script for BTG Pactual Funds API
Populates the database with initial funds and demo user
"""

import asyncio
from datetime import datetime
from passlib.context import CryptContext

from .connection import connect_to_mongo, get_funds_collection, get_users_collection
from ..models import Fund, User, FundCategory, NotificationPreference, UserRole

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Initial funds data based on the provided image
INITIAL_FUNDS = [
    {
        "name": "FPV_BTG_PACTUAL_RECAUDADORA",
        "category": FundCategory.FPV,
        "minimum_amount": 75000,
        "is_active": True
    },
    {
        "name": "FPV_BTG_PACTUAL_ECOPETROL",
        "category": FundCategory.FPV,
        "minimum_amount": 125000,
        "is_active": True
    },
    {
        "name": "DEUDAPRIVADA",
        "category": "FIC",  # Will be converted to enum
        "minimum_amount": 50000,
        "is_active": True
    },
    {
        "name": "FDO-ACCIONES",
        "category": "FIC",  # Will be converted to enum  
        "minimum_amount": 250000,
        "is_active": True
    },
    {
        "name": "FPV_BTG_PACTUAL_DINAMICA",
        "category": FundCategory.FPV,
        "minimum_amount": 100000,
        "is_active": True
    }
]

# Demo user data
DEMO_USER = {
    "email": "demo@btgpactual.com",
    "phone": "+573001234567",
    "full_name": "Usuario Demo BTG",
    "balance": 500000,
    "notification_preference": NotificationPreference.EMAIL,
    "subscribed_funds": [],
    "role": UserRole.CLIENT,
    "is_active": True,
    "password": "demo123"  # Will be hashed
}

async def seed_funds():
    """Insert initial funds data"""
    funds_collection = get_funds_collection()
    
    # Check if funds already exist
    existing_count = await funds_collection.count_documents({})
    if existing_count > 0:
        print(f"ℹ️  Funds already exist ({existing_count} found). Skipping seed...")
        return
    
    print("🌱 Seeding initial funds data...")
    
    # Prepare funds data
    funds_data = []
    for fund_data in INITIAL_FUNDS:
        fund_dict = fund_data.copy()
        fund_dict["created_at"] = datetime.utcnow()
        
        # Handle FIC category (not in enum)
        if fund_dict["category"] == "FIC":
            fund_dict["category"] = "FIDUCIARIO"  # Map to existing enum
        
        funds_data.append(fund_dict)
    
    # Insert funds
    result = await funds_collection.insert_many(funds_data)
    print(f"✅ Inserted {len(result.inserted_ids)} funds successfully")

async def seed_demo_user():
    """Insert demo user"""
    users_collection = get_users_collection()
    
    # Check if demo user already exists
    existing_user = await users_collection.find_one({"email": DEMO_USER["email"]})
    if existing_user:
        print("ℹ️  Demo user already exists. Skipping...")
        return
    
    print("🌱 Creating demo user...")
    
    # Prepare user data
    user_data = DEMO_USER.copy()
    user_data["created_at"] = datetime.utcnow()
    
    # Hash password
    hashed_password = pwd_context.hash(user_data.pop("password"))
    user_data["password"] = hashed_password
    
    # Insert user
    result = await users_collection.insert_one(user_data)
    print(f"✅ Demo user created successfully")
    print(f"📧 Login credentials: {DEMO_USER['email']} / demo123")

async def seed_database():
    """Main seeding function"""
    print("🚀 Starting database seeding...")
    
    try:
        # Connect to database
        await connect_to_mongo()
        
        # Seed data
        await seed_funds()
        await seed_demo_user()
        
        print("🎉 Database seeding completed successfully!")
        
    except Exception as e:
        print(f"❌ Error seeding database: {e}")
        raise e

async def clear_database():
    """Clear all data (for development only)"""
    print("⚠️  CLEARING ALL DATABASE DATA...")
    
    try:
        await connect_to_mongo()
        
        funds_collection = get_funds_collection()
        users_collection = get_users_collection()
        
        # Clear collections
        await funds_collection.delete_many({})
        await users_collection.delete_many({})
        
        print("🗑️  Database cleared successfully")
        
    except Exception as e:
        print(f"❌ Error clearing database: {e}")
        raise e

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--clear":
        asyncio.run(clear_database())
    else:
        asyncio.run(seed_database())