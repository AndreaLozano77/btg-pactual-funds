# app/services/fund_service.py - VERSIÓN CORREGIDA
from fastapi import HTTPException, status
from typing import List, Optional
from app.models.fund import Fund, FundCreate
from app.models.transaction import Transaction, TransactionCreate, TransactionHistory, TransactionType, TransactionStatus
from app.models.user_balance import UserBalance, SubscriptionRequest, CancellationRequest
from app.database.connection import get_database  # CORREGIDO
from datetime import datetime
import uuid
import logging

logger = logging.getLogger(__name__)

class FundService:
    """Service layer for fund-related business logic"""
    
    @staticmethod
    async def get_all_funds() -> List[Fund]:
        """Get all active funds"""
        try:
            db = get_database()
            funds_cursor = db.funds.find({"is_active": True})
            funds = await funds_cursor.to_list(length=None)  # length en lugar de None
            return [Fund(**fund) for fund in funds]
        except Exception as e:
            logger.error(f"Error getting all funds: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error retrieving funds"
            )
    
    @staticmethod
    async def get_fund_by_id(fund_id: str) -> Optional[Fund]:
        """Get fund by ID"""
        try:
            db = get_database()
            fund = await db.funds.find_one({"_id": fund_id})
            if fund:
                return Fund(**fund)
            return None
        except Exception as e:
            logger.error(f"Error getting fund by ID: {e}")
            return None
    
    @staticmethod
    async def create_fund(fund_data: FundCreate) -> Fund:
        """Create a new fund"""
        try:
            db = get_database()
            
            # Check if fund name already exists
            existing_fund = await db.funds.find_one({"name": fund_data.name})
            if existing_fund:
                raise ValueError(f"Fund with name '{fund_data.name}' already exists")
            
            fund_dict = fund_data.dict()
            fund_dict.update({
                "_id": str(uuid.uuid4()),
                "created_at": datetime.utcnow(),  # ✅ CORREGIDO: usar utcnow()
                "is_active": True
            })
            
            result = await db.funds.insert_one(fund_dict)
            created_fund = await db.funds.find_one({"_id": fund_dict["_id"]})
            
            logger.info(f"Fund created: {fund_data.name}")
            return Fund(**created_fund)
        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Error creating fund: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error creating fund"
            )
    
    @staticmethod
    async def get_user_balance(user_id: str) -> UserBalance:
        """Get user balance and portfolio"""
        try:
            db = get_database()
            
            # Get user
            user = await db.users.find_one({"_id": user_id})
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
            
            # Calculate subscribed funds value
            subscribed_value = 0
            if user.get("subscribed_funds"):
                transactions = db.transactions.find({
                    "user_id": user_id,
                    "status": "COMPLETED"
                })
                async for transaction in transactions:
                    if transaction["transaction_type"] == "SUBSCRIPTION":
                        subscribed_value += transaction["amount"]
                    elif transaction["transaction_type"] == "CANCELLATION":
                        subscribed_value -= transaction["amount"]
            
            available_balance = user.get("balance", 0)
            
            return UserBalance(
                user_id=user_id,
                current_balance=available_balance + subscribed_value,
                available_balance=available_balance,
                subscribed_funds_value=subscribed_value
            )
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting user balance: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error retrieving balance"
            )
    
    @staticmethod
    async def subscribe_to_fund(user_id: str, subscription: SubscriptionRequest) -> Transaction:
        """Subscribe user to a fund"""
        try:
            db = get_database()
            
            # Validate fund exists
            fund = await db.funds.find_one({"_id": subscription.fund_id})
            if not fund:
                raise ValueError("Fund not found")
            
            if not fund.get("is_active"):
                raise ValueError("Fund is not active")
            
            # Get user
            user = await db.users.find_one({"_id": user_id})
            if not user:
                raise ValueError("User not found")
            
            # Validate minimum amount
            if subscription.amount < fund["minimum_amount"]:
                raise ValueError(
                    f"No tiene saldo disponible para vincularse al fondo {fund['name']}. "
                    f"Monto mínimo requerido: COP ${fund['minimum_amount']:,}"
                )
            
            # Check available balance
            if user.get("balance", 0) < subscription.amount:
                raise ValueError(f"No tiene saldo disponible para vincularse al fondo {fund['name']}")
            
            # Create transaction
            transaction_id = f"TXN_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{user_id[:6]}"
            transaction_dict = {
                "_id": str(uuid.uuid4()),
                "transaction_id": transaction_id,
                "user_id": user_id,
                "fund_id": subscription.fund_id,
                "fund_name": fund["name"],
                "transaction_type": TransactionType.SUBSCRIPTION,
                "amount": subscription.amount,
                "status": TransactionStatus.COMPLETED,  # ✅ CORREGIDO: usar enum
                "created_at": datetime.utcnow(),
                "completed_at": datetime.utcnow()
            }
            
            # Use MongoDB transaction for data consistency
            async with await db.client.start_session() as session:
                async with session.start_transaction():
                    try:
                        # Insert transaction
                        await db.transactions.insert_one(transaction_dict, session=session)
                        
                        # Update user balance
                        new_balance = user["balance"] - subscription.amount
                        await db.users.update_one(
                            {"_id": user_id},
                            {
                                "$set": {"balance": new_balance, "updated_at": datetime.utcnow()},
                                "$addToSet": {"subscribed_funds": subscription.fund_id}
                            },
                            session=session
                        )
                        
                    except Exception as e:
                        logger.error(f"Transaction failed: {e}")
                        raise
            
            logger.info(f"User {user_id} subscribed to fund {subscription.fund_id}")
            return Transaction(**transaction_dict)
            
        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Error in fund subscription: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error processing subscription"
            )
    
    @staticmethod
    async def cancel_fund_subscription(user_id: str, cancellation: CancellationRequest) -> Transaction:
        """Cancel fund subscription"""
        try:
            db = get_database()
            
            # Validate fund exists
            fund = await db.funds.find_one({"_id": cancellation.fund_id})
            if not fund:
                raise ValueError("Fund not found")
            
            # Get user
            user = await db.users.find_one({"_id": user_id})
            if not user:
                raise ValueError("User not found")
            
            # Check if user is subscribed to this fund
            if cancellation.fund_id not in user.get("subscribed_funds", []):
                raise ValueError(f"User is not subscribed to fund {fund['name']}")
            
            # Calculate current investment in this fund
            invested_amount = 0
            transactions = db.transactions.find({
                "user_id": user_id,
                "fund_id": cancellation.fund_id,
                "status": "COMPLETED"
            })
            
            async for transaction in transactions:
                if transaction["transaction_type"] == "SUBSCRIPTION":
                    invested_amount += transaction["amount"]
                elif transaction["transaction_type"] == "CANCELLATION":
                    invested_amount -= transaction["amount"]
            
            if invested_amount <= 0:
                raise ValueError(f"No active investment found in fund {fund['name']}")
            
            # Create cancellation transaction
            transaction_id = f"TXN_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{user_id[:6]}"
            transaction_dict = {
                "_id": str(uuid.uuid4()),
                "transaction_id": transaction_id,
                "user_id": user_id,
                "fund_id": cancellation.fund_id,
                "fund_name": fund["name"],
                "transaction_type": TransactionType.CANCELLATION,
                "amount": invested_amount,
                "status": TransactionStatus.COMPLETED,
                "created_at": datetime.utcnow(),
                "completed_at": datetime.utcnow()
            }
            
            # Use MongoDB transaction for data consistency
            async with await db.client.start_session() as session:
                async with session.start_transaction():
                    try:
                        # Insert cancellation transaction
                        await db.transactions.insert_one(transaction_dict, session=session)
                        
                        # Return money to user
                        new_balance = user["balance"] + invested_amount
                        await db.users.update_one(
                            {"_id": user_id},
                            {
                                "$set": {"balance": new_balance, "updated_at": datetime.utcnow()},
                                "$pull": {"subscribed_funds": cancellation.fund_id}
                            },
                            session=session
                        )
                        
                    except Exception as e:
                        logger.error(f"Cancellation transaction failed: {e}")
                        raise
            
            logger.info(f"User {user_id} cancelled subscription to fund {cancellation.fund_id}")
            return Transaction(**transaction_dict)
            
        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Error in fund cancellation: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error processing cancellation"
            )
    
    @staticmethod
    async def get_user_transaction_history(user_id: str) -> TransactionHistory:
        """Get user transaction history"""
        try:
            db = get_database()
            
            # Get all user transactions
            transactions_cursor = db.transactions.find(
                {"user_id": user_id}
            ).sort("created_at", -1)
            
            transactions = []
            total_invested = 0
            
            async for transaction in transactions_cursor:
                transactions.append(Transaction(**transaction))
                if transaction["status"] == "COMPLETED":
                    if transaction["transaction_type"] == "SUBSCRIPTION":
                        total_invested += transaction["amount"]
                    elif transaction["transaction_type"] == "CANCELLATION":
                        total_invested -= transaction["amount"]
            
            # Get current balance
            user = await db.users.find_one({"_id": user_id})
            available_balance = user.get("balance", 0) if user else 0
            
            return TransactionHistory(
                user_id=user_id,  # ✅ AGREGADO: campo faltante
                transactions=transactions,
                total_invested=max(0, total_invested),
                available_balance=available_balance,
                total_transactions=len(transactions)
            )
            
        except Exception as e:
            logger.error(f"Error getting transaction history: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error retrieving transaction history"
            )
    
    @staticmethod
    async def initialize_default_funds():
        """Initialize system with default BTG funds"""
        try:
            db = get_database()
            
            # Check if funds already exist
            fund_count = await db.funds.count_documents({})
            if fund_count > 0:
                logger.info("Funds already initialized, skipping...")
                return
            
            from app.models.fund import FundCategory
            default_funds = [
                {"name": "FPV_BTG_PACTUAL_RECAUDADORA", "minimum_amount": 75000, "category": FundCategory.FPV},
                {"name": "FPV_BTG_PACTUAL_ECOPETROL", "minimum_amount": 125000, "category": FundCategory.FPV},
                {"name": "DEUDAPRIVADA", "minimum_amount": 50000, "category": FundCategory.FIC},
                {"name": "FDO-ACCIONES", "minimum_amount": 250000, "category": FundCategory.FIC},
                {"name": "FPV_BTG_PACTUAL_DINAMICA", "minimum_amount": 100000, "category": FundCategory.FPV}
            ]
            
            for fund_data in default_funds:
                try:
                    await FundService.create_fund(FundCreate(**fund_data))
                    logger.info(f"Created default fund: {fund_data['name']}")
                except ValueError:
                    logger.info(f"Fund {fund_data['name']} already exists, skipping...")
                    
            logger.info("✅ Default funds initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing default funds: {e}")