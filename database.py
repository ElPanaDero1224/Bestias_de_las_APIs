from sqlalchemy import create_engine, MetaData
from databases import Database

# Configura la URL de la base de datos (modifica según tu necesidad)
DATABASE_URL = "mysql+aiomysql://pablo:sala321-@localhost:3306/sistemaintegral"
DATABASE_URL2 = "mysql+aiomysql://root:Es_el_de_halo_5@localhost:3306/proyectose"


# Crea el motor de SQLAlchemy y la conexión asíncrona
database = Database(DATABASE_URL)
metadata = MetaData()
engine = create_engine(DATABASE_URL, pool_size=10, max_overflow=20)

database2 = Database(DATABASE_URL2)
engine2 = create_engine(DATABASE_URL2, pool_size=10, max_overflow=20)