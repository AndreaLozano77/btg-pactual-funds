# scripts/populate_funds.py
import asyncio
import sys
import os

# Añadir el directorio raíz al path para imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from motor.motor_asyncio import AsyncIOMotorClient
from app.models.fund import Fund, FundCategory
from datetime import datetime

# Datos de los fondos según la tabla del enunciado
INITIAL_FUNDS = [
    {
        "name": "FPV_BTG_PACTUAL_RECAUDADORA",
        "minimum_amount": 75000,
        "category": FundCategory.FPV
    },
    {
        "name": "FPV_BTG_PACTUAL_ECOPETROL",
        "minimum_amount": 125000,
        "category": FundCategory.FPV
    },
    {
        "name": "DEUDAPRIVADA",
        "minimum_amount": 50000,
        "category": FundCategory.FIC
    },
    {
        "name": "FDO-ACCIONES",
        "minimum_amount": 250000,
        "category": FundCategory.FIC
    },
    {
        "name": "FPV_BTG_PACTUAL_DINAMICA",
        "minimum_amount": 100000,
        "category": FundCategory.FPV
    }
]

async def populate_funds():
    """Poblar la base de datos con los fondos iniciales"""
    
    # Conectar a MongoDB
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    database = client.btg_funds
    funds_collection = database.get_collection("funds")
    
    try:
        # Limpiar colección existente (opcional)
        print("🧹 Limpiando fondos existentes...")
        await funds_collection.delete_many({})
        
        # Insertar fondos
        print("💰 Insertando fondos iniciales...")
        
        for fund_data in INITIAL_FUNDS:
            fund_doc = {
                **fund_data,
                "is_active": True,
                "created_at": datetime.now()
            }
            
            result = await funds_collection.insert_one(fund_doc)
            print(f"✅ Creado fondo: {fund_data['name']} - ID: {result.inserted_id}")
        
        # Verificar inserción
        count = await funds_collection.count_documents({})
        print(f"\n🎉 Total de fondos en la base de datos: {count}")
        
        # Mostrar fondos creados
        print("\n📋 Fondos disponibles:")
        cursor = funds_collection.find({})
        async for fund in cursor:
            print(f"   • {fund['name']} - Mínimo: COP ${fund['minimum_amount']:,} - Categoría: {fund['category']}")
            
    except Exception as e:
        print(f"❌ Error al poblar fondos: {e}")
    finally:
        client.close()
        print("\n🔌 Conexión cerrada")

if __name__ == "__main__":
    print("🚀 Iniciando población de fondos BTG Pactual...")
    asyncio.run(populate_funds())