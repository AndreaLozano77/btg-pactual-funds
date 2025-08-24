 # BTG Pactual Funds API

API construida con FastAPI y MongoDB para la gestión de fondos de BTG Pactual.

## Prerrequisitos

Antes de comenzar, asegurarse de tener instalado en tu sistema:
*   Python 3.11
*   MongoDB (local o una instancia remota como MongoDB Atlas)
*   Git

## Cómo ejecutar el proyecto localmente

Pasos para ejecutar el servidor de desarrollo en su máquina.

1.  **Clonar el repositorio**
    ```bash
    git clone https://github.com/AndreaLozano77/btg-pactual-funds.git
    cd btg-pactual-funds/app
    ```

2.  **Crear y activar un entorno virtual**
    Este proyecto utiliza un entorno virtual llamado `venv311`. Para crearlo y activarlo:

    ```bash
    # Crear el entorno virtual
    python -m venv venv311

    # Activarlo (el comando depende de su terminal)
    # Para Windows (PowerShell):
    .\venv311\Scripts\activate
    # Para Windows (CMD):
    .\venv311\Scripts\activate.bat
    # Para Mac/Linux:
    source venv311/bin/activate
    ```

    *(Su terminal debería mostrar ahora `(venv311)` al principio de la línea, indicando que el entorno está activo).*

3.  **Instalar las dependencias**
    Con el entorno virtual activado, instale todas las librerías necesarias:

    ```bash
    pip install -r requirements.txt
    ```

4.  **Configurar las variables de entorno**
    *   Haga una copia del archivo `env.example` y renómbrela a `.env`.
    *   Abre el archivo `.env` con un editor de texto.
    *   **Crucial:** Complete la variable `MONGODB_URL` con la cadena de conexión a su base de datos MongoDB.
        *   Si MongoDB está instalado en su misma computadora, usualmente es: `mongodb://localhost:27017/btg-funds-db`
    *   Configura cualquier otra variable que necesite (como `JWT_SECRET_KEY`).

5.  **Ejecutar la aplicación**
    Todo listo. Ahora puede levantar el servidor:

    ```bash
    uvicorn main:app --reload --port 8000
    ```

6.  **Probar la API**
    Abrir el navegador web y visitar las siguientes direcciones:
    *   **Interfaz interactiva de documentation (Swagger UI):** http://localhost:8000/docs
    *   **Documentación alternativa (ReDoc):** http://localhost:8000/redoc

    Desde aquí se pueden ver todos los endpoints y probarlos directamente.