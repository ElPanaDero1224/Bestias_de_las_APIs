from sqlalchemy import create_engine, MetaData
from databases import Database
from decouple import config
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi import Request
from datetime import datetime, timedelta
from database import database
from sqlalchemy import select, Table, MetaData
from fastapi.middleware.cors import CORSMiddleware
import redis
from itsdangerous import URLSafeTimedSerializer
from decouple import config



DATABASE_URL = config("DATABASE_URL")

# Añadir esta línea para forzar el protocolo antiguo
FORCED_MYSQL_CONFIG = {
    "init_command": "SET SESSION sql_mode='STRICT_TRANS_TABLES'",
    "connect_timeout": 10
}

database = Database(DATABASE_URL, **FORCED_MYSQL_CONFIG)
metadata = MetaData()

# Usar pool_pre_ping para mantener la conexión activa
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
    connect_args={"connect_timeout": 10}
)

app = FastAPI()

@app.on_event("startup")
async def startup():
    app.state.db1_status = False
    try:
        # Verificar conexión ejecutando una consulta simple
        await database.execute("SELECT 1")
        app.state.db1_status = True
        print("✅ Conexión a la base de datos exitosa")
    except Exception as e:
        print(f"❌ Error de conexión: {str(e)}")
        # Sugerencias de solución comunes
        if "Access denied" in str(e):
            print("Verifica usuario y contraseña")
        elif "Can't connect" in str(e):
            print("Verifica red/puerto/firewall")
        elif "Unknown database" in str(e):
            print("Verifica nombre de la base de datos")