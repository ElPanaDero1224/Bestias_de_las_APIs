from sqlalchemy import create_engine, MetaData
from databases import Database

# Configura la URL de la base de datos (modifica según tu necesidad)
DATABASE_URL = "mysql+aiomysql://root:@localhost:3306/sistemaintegral"

# Crea el motor de SQLAlchemy y la conexión asíncrona
database = Database(DATABASE_URL)
metadata = MetaData()
engine = create_engine(DATABASE_URL, pool_size=10, max_overflow=20)

