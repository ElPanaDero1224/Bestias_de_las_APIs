from sqlalchemy import create_engine, MetaData
from databases import Database
from decouple import config

DATABASE_URL = config("DATABASE_URL")

# Crea el motor de SQLAlchemy y la conexión asíncrona
database = Database(DATABASE_URL)
metadata = MetaData()
engine = create_engine(DATABASE_URL, pool_size=10, max_overflow=20)