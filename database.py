from sqlalchemy import create_engine, MetaData
from decouple import config

DATABASE_URL = config("DATABASE_URL").replace("aiomysql", "pymysql")  # Cambia el driver

# Conexión síncrona
engine = create_engine(DATABASE_URL, pool_size=10, max_overflow=20)
metadata = MetaData()