#Instalaciones
""" pip install fastapi uvicorn sqlalchemy asyncmy """



from fastapi import FastAPI
from database import database

app = FastAPI()

# 🚀 Conectar la base de datos cuando la API se inicia
@app.on_event("startup")
async def startup():
    await database.connect()

# 🛑 Desconectar la base de datos cuando la API se detiene
@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()

# 🌐 Ruta de prueba para verificar la conexión
@app.get("/")
async def root():
    return {"message": "¡Conexión exitosa a la base de datos!"}