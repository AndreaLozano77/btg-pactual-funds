from fastapi import HTTPException, status
from app.models.fund import Fund, FundCreate
from app.models.transaction import Transaction, TransactionCreate, TransactionHistory, TransactionType
from app.models.user_balance import UserBalance, SubscriptionRequest, CancellationRequest
from app.database import get_database
from datetime import datetime
import uuid
import logging

logger = logging.getLogger(__name__)

class FundService:
    """Service layer for fund-related business logic"""
    
    def __init__(self):
        self.db = None
    
    async def get_database(self):
        """Get database connection"""
        if not self.db:
            self.db = await get_database()
        return self.db
    
    async def get_all_funds(self) -> List[Fund]:
        """Get all active funds"""
        try:
            db = await self.get_database()
            funds_cursor = db.funds.find({"is_active": True})
            funds = await funds_cursor.to_list(None)
            return [Fund(**fund) for fund in funds]
        except Exception as e:
            logger.error(f"Error getting all funds: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error retrieving funds"
            )
    
    async def get_fund_by_id(self, fund_id: str) -> Optional[Fund]:
        """Get fund by ID"""
        try:
            db = await self.get_database()
            fund = await db.funds.find_one({"_id": fund_id})
            if fund:
                return Fund(**fund)
            return None
        except Exception as e:
            logger.error(f"Error getting fund by ID: {e}")
            return None
    
    async def create_fund(self, fund_data: FundCreate) -> Fund:
        """Create a new fund"""
        try:
            db = await self.get_database()
            fund_dict = fund_data.dict()
            fund_dict["_id"] = str(uuid.uuid4())
            fund_dict["created_at"] = datetime.now()
            fund_dict["is_active"] = True
            
            result = await db.funds.insert_one(fund_dict)
            created_fund = await db.funds.find_one({"_id": result.inserted_id})
            return Fund(**created_fund)
        except Exception as e:
            logger.error(f"Error creating fund: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error creating fund"
            )
    
    async def get_user_balance(self, user_id: str) -> UserBalance:
        """Get user balance and portfolio"""
        try:
            db = await self.get_database()
            
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
    
    async def subscribe_to_fund(self, user_id: str, subscription: SubscriptionRequest) -> Transaction:
        """Subscribe user to a fund"""
        try:
            db = await self.get_database()
            
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
                raise ValueError(f"Minimum investment amount is {fund['minimum_amount']}")
            
            # Check available balance
            if user.get("balance", 0) < subscription.amount:
                raise ValueError(f"No tiene saldo disponible para vincularse al fondo {fund['name']}")
            
            # Create transaction
            transaction_dict = {
                "_id": str(uuid.uuid4()),
                "transaction_id": str(uuid.uuid4()),
                "user_id": user_id,
                "fund_id": subscription.fund_id,
                "fund_name": fund["name"],
                "transaction_type": TransactionType.SUBSCRIPTION,
                "amount": subscription.amount,
                "status": "COMPLETED",
                "created_at": datetime.now(),
                "completed_at": datetime.now()
            }
            
            # Start transaction (simulate database transaction)
            await db.transactions.insert_one(transaction_dict)
            
            # Update user balance
            new_balance = user["balance"] - subscription.amount
            await db.users.update_one(
                {"_id": user_id},
                {
                    "$set": {"balance": new_balance},
                    "$addToSet": {"subscribed_funds": subscription.fund_id}
                }
            )
            
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
    
    async def cancel_fund_subscription(self, user_id: str, cancellation: CancellationRequest) -> Transaction:
        """Cancel fund subscription"""
        try:
            db = await self.get_database()
            
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
                raise ValueError("User is not subscribed to this fund")
            
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
                raise ValueError("No active investment in this fund")
            
            # Create cancellation transaction
            transaction_dict = {
                "_id": str(uuid.uuid4()),
                "transaction_id": str(uuid.uuid4()),
                "user_id": user_id,
                "fund_id": cancellation.fund_id,
                "fund_name": fund["name"],
                "transaction_type": TransactionType.CANCELLATION,
                "amount": invested_amount,
                "status": "COMPLETED",
                "created_at": datetime.now(),
                "completed_at": datetime.now()
            }
            
            # Process cancellation
            await db.transactions.insert_one(transaction_dict)
            
            # Return money to user
            new_balance = user["balance"] + invested_amount
            await db.users.update_one(
                {"_id": user_id},
                {
                    "$set": {"balance": new_balance},
                    "$pull": {"subscribed_funds": cancellation.fund_id}
                }
            )
            
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
    
    async def get_user_transaction_history(self, user_id: str) -> TransactionHistory:
        """Get user transaction history"""
        try:
            db = await self.get_database()
            
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