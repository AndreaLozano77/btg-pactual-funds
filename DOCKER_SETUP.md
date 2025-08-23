# 🐳 Docker Setup - BTG Pactual Funds API

## 📋 Requisitos Previos

- [Docker](https://docs.docker.com/get-docker/) (versión 20.10 o superior)
- [Docker Compose](https://docs.docker.com/compose/install/) (versión 2.0 o superior)

## 🚀 Ejecución Rápida

### 1. Clonar y Configurar
```bash
# Copiar variables de entorno
cp .env.example .env

# Verificar que Docker esté corriendo
docker --version
docker-compose --version
```

### 2. Levantar los Servicios
```bash
# Construir y ejecutar todos los servicios
docker-compose up --build

# O en background
docker-compose up -d --build
```

### 3. Verificar que Todo Funcione
```bash
# Verificar contenedores
docker-compose ps

# Ver logs de la API
docker-compose logs api

# Ver logs de MongoDB
docker-compose logs mongodb
```

## 🌐 Servicios Disponibles

| Servicio | URL | Descripción | Credenciales |
|----------|-----|-------------|-------------|
| **API** | http://localhost:8000 | FastAPI Application | - |
| **API Docs** | http://localhost:8000/docs | Swagger UI | - |
| **MongoDB** | mongodb://localhost:27017 | Base de datos | admin/btgpactual2025 |
| **Mongo Express** | http://localhost:8081 | GUI de MongoDB | btg/pactual |

## 👤 Usuario Demo

El sistema viene con un usuario demo preconfigurado:

- **Email:** demo@btgpactual.com
- **Password:** demo123
- **Saldo inicial:** COP $500,000

## 💰 Fondos Precargados

| Fondo | Categoría | Monto Mínimo |
|-------|-----------|--------------|
| FPV_BTG_PACTUAL_RECAUDADORA | FPV | $75,000 |
| FPV_BTG_PACTUAL_ECOPETROL | FPV | $125,000 |
| DEUDAPRIVADA | FIC | $50,000 |
| FDO-ACCIONES | FIC | $250,000 |
| FPV_BTG_PACTUAL_DINAMICA | FPV | $100,000 |

## 🔧 Comandos Útiles

### Reiniciar Servicios
```bash
# Parar servicios
docker-compose down

# Reiniciar con reconstrucción
docker-compose up --build
```

### Limpiar Base de Datos
```bash
# Eliminar volúmenes (CUIDADO: borra toda la data)
docker-compose down -v

# Volver a crear desde cero
docker-compose up --build
```

### Logs y Debugging
```bash
# Ver logs en tiempo real
docker-compose logs -f api

# Entrar al contenedor de la API
docker-compose exec api bash

# Entrar a MongoDB
docker-compose exec mongodb mongosh -u admin -p btgpactual2025
```

### Tests
```bash
# Ejecutar tests dentro del contenedor
docker-compose exec api python -m pytest

# Ejecutar tests con coverage
docker-compose exec api python -m pytest --cov=app
```

## 📊 Verificación de Funcionamiento

### 1. Health Check
```bash
curl http://localhost:8000/health
```

### 2. Listar Fondos
```bash
curl http://localhost:8000/api/v1/funds/
```

### 3. Login Demo
```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "demo@btgpactual.com",
    "password": "demo123"
  }'
```

## 🛠️ Solución de Problemas

### Puerto Ocupado
```bash
# Cambiar puerto en docker-compose.yml
ports:
  - "8001:8000"  # API
  - "27018:27017"  # MongoDB
  - "8082:8081"  # Mongo Express
```

### Problemas de Conexión MongoDB
```bash
# Verificar logs de MongoDB
docker-compose logs mongodb

# Reiniciar solo MongoDB
docker-compose restart mongodb
```

### Limpiar Todo
```bash
# Eliminar contenedores, volúmenes e imágenes
docker-compose down -v --rmi all
docker system prune -a
```

## 📝 Notas para el Profesor

- ✅ **Zero configuration**: Solo necesita `docker-compose up`
- ✅ **Datos demo**: Usuario y fondos precargados
- ✅ **Documentación**: Swagger UI automático
- ✅ **Logs**: Fáciles de revisar con `docker-compose logs`
- ✅ **Portable**: Funciona en cualquier OS con Docker

### Evaluación Rápida
1. `docker-compose up -d`
2. Abrir http://localhost:8000/docs
3. Usar credenciales demo para probar endpoints
4. Ver base de datos en http://localhost:8081

¡El proyecto estará completamente funcional en menos de 2 minutos! 🚀