from fastapi import FastAPI, Depends
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

app = FastAPI()

# Configuración de conexiones
DATABASE_URL_1 = "mysql+asyncmy://root:Es_el_de_halo_5@localhost/sistemaintegral"
DATABASE_URL_2 = "mysql+asyncmy://user:password@host2/db2"

engine_1 = create_async_engine(DATABASE_URL_1, echo=True)
engine_2 = create_async_engine(DATABASE_URL_2, echo=True)

SessionLocal_1 = sessionmaker(bind=engine_1, class_=AsyncSession, expire_on_commit=False)
SessionLocal_2 = sessionmaker(bind=engine_2, class_=AsyncSession, expire_on_commit=False)

async def get_db_1():
    async with SessionLocal_1() as session:
        yield session

async def get_db_2():
    async with SessionLocal_2() as session:
        yield session

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.get("/check_db")
async def check_db(session_1: AsyncSession = Depends(get_db_1), session_2: AsyncSession = Depends(get_db_2)):
    try:
        await session_1.execute("SELECT 1")
        db1_status = "Connected"
    except Exception:
        db1_status = "Not Connected"

    try:
        await session_2.execute("SELECT 1")
        db2_status = "Connected"
    except Exception:
        db2_status = "Not Connected"

    return {"Database 1": db1_status, "Database 2": db2_status}
