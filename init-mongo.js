// Create collections
db.createCollection('users');
db.createCollection('funds');
db.createCollection('transactions');

print('✅ Collections created successfully');

// Insert initial funds data based on the provided image
db.funds.insertMany([
  {
    name: "FPV_BTG_PACTUAL_RECAUDADORA",
    category: "FPV",
    minimum_amount: 75000,
    is_active: true,
    created_at: new Date()
  },
  {
    name: "FPV_BTG_PACTUAL_ECOPETROL",
    category: "FPV", 
    minimum_amount: 125000,
    is_active: true,
    created_at: new Date()
  },
  {
    name: "DEUDAPRIVADA",
    category: "FIC",
    minimum_amount: 50000,
    is_active: true,
    created_at: new Date()
  },
  {
    name: "FDO-ACCIONES", 
    category: "FIC",
    minimum_amount: 250000,
    is_active: true,
    created_at: new Date()
  },
  {
    name: "FPV_BTG_PACTUAL_DINAMICA",
    category: "FPV",
    minimum_amount: 100000,
    is_active: true,
    created_at: new Date()
  }
]);

print('✅ Initial funds data inserted successfully');

// Create indexes for better performance
db.users.createIndex({ "email": 1 }, { unique: true });
db.users.createIndex({ "created_at": 1 });

db.funds.createIndex({ "name": 1 }, { unique: true });
db.funds.createIndex({ "category": 1 });
db.funds.createIndex({ "is_active": 1 });

db.transactions.createIndex({ "transaction_id": 1 }, { unique: true });
db.transactions.createIndex({ "user_id": 1 });
db.transactions.createIndex({ "fund_id": 1 });
db.transactions.createIndex({ "created_at": -1 });
db.transactions.createIndex({ "user_id": 1, "created_at": -1 });

print('✅ Database indexes created successfully');

// Insert a demo user for testing
db.users.insertOne({
  email: "demo@btgpactual.com",
  phone: "+573001234567",
  full_name: "Usuario Demo",
  balance: 500000,
  notification_preference: "email",
  subscribed_funds: [],
  role: "client",
  is_active: true,
  password: "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewmyKq2G..1PQO1u", // password: "demo123"
  created_at: new Date()
});

print('✅ Demo user created successfully');
print('📧 Demo user credentials: demo@btgpactual.com / demo123');

print('🎉 MongoDB initialization completed!');
print('🌐 Available services:');
print('   - API: http://localhost:8000');
print('   - API Docs: http://localhost:8000/docs');
print('   - Mongo Express: http://localhost:8081 (btg/pactual)');