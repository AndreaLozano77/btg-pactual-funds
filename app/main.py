# main.py - CON CONEXIÓN MONGODB AUTOMÁTICA
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from datetime import datetime
import logging

# Import routes
from app.routes import user_routes, fund_routes

# Import database connection
from app.database.connection import connect_to_mongo, close_mongo_connection

# Import services for initialization
from app.services.fund_service import FundService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    logger.info("🚀 Starting BTG Pactual Funds API...")
    try:
        # Connect to MongoDB
        await connect_to_mongo()
        
        # Initialize default funds
        await FundService.initialize_default_funds()
        
        logger.info("✅ Application startup completed successfully")
        yield
    except Exception as e:
        logger.error(f"❌ Startup error: {e}")
        raise
    finally:
        # Shutdown
        logger.info("🔄 Shutting down BTG Pactual Funds API...")
        await close_mongo_connection()
        logger.info("✅ Application shutdown completed")

# Create FastAPI app with lifespan
app = FastAPI(
    title="BTG Pactual Funds API",
    description="API empresarial para gestión de fondos de inversión BTG Pactual",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan  # ✅ CRÍTICO: Esto conecta a MongoDB
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Temporalmente permisivo para desarrollo
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check endpoint
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now(),
        "service": "BTG Pactual Funds API",
        "version": "2.0.0"
    }

@app.get("/")
async def root():
    return {
        "message": "BTG Pactual Funds API",
        "version": "2.0.0",
        "status": "active",
        "documentation": "/docs"
    }

# Test database endpoint
@app.get("/test-db")
async def test_database():
    try:
        from app.database.connection import get_database
        db = get_database()  # ✅ CORREGIDO
        
        # Test basic operation
        result = await db.command("ping")
        
        # Count collections
        user_count = await db.users.count_documents({})
        fund_count = await db.funds.count_documents({})
        
        return {
            "status": "connected",
            "ping": result,
            "collections": {
                "users": user_count,
                "funds": fund_count
            },
            "database_name": db.name
        }
    except Exception as e:
        logger.error(f"Database test error: {e}")
        return {
            "status": "error",
            "error": str(e),
            "error_type": type(e).__name__
        }

# Include routers
app.include_router(user_routes.router)
app.include_router(fund_routes.router)

# Run the application
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)