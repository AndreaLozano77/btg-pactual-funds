# main.py - VERSIÓN MÍNIMA SEGURA
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import logging

# Import routes
from app.routes import user_routes

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="BTG Pactual Funds API",
    description="API empresarial para gestión de fondos de inversión BTG Pactual",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
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

# Include routers
app.include_router(user_routes.router)

# Run the application
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)