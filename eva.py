from sqlalchemy import create_engine, MetaData
from databases import Database
from decouple import config
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi import Request
from datetime import datetime, timedelta
from sqlalchemy import select, Table, MetaData
from fastapi.middleware.cors import CORSMiddleware
import redis
from itsdangerous import URLSafeTimedSerializer

# Cargar variables de entorno
DATABASE_URL = config("DATABASE_URL")

# Configuración de la base de datos
database = Database(DATABASE_URL)
metadata = MetaData()

# Motor de SQLAlchemy
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
        await database.connect()
        app.state.db1_status = True
        print("✅ Conexión a la base de datos exitosa")
    except Exception as e:
        print(f"❌ Error de conexión: {str(e)}")

@app.on_event("shutdown")
async def shutdown():
    if app.state.db1_status:
        await database.disconnect()

@app.get("/")
def read_root():
    return {"message": "¡Hola, Mundo!"}