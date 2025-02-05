# Instalaciones necesarias:
# pip install fastapi uvicorn sqlalchemy asyncmy 

from fastapi import FastAPI
from database import database, database2
from sqlalchemy import select, Table, MetaData

app = FastAPI()

# 🚀 Conectar la base de datos cuando la API se inicia
@app.on_event("startup")
async def startup():
    app.state.db1_status = False
    app.state.db2_status = False

    try:
        await database.connect()
        app.state.db1_status = True
    except Exception as e:
        print(f"❌ Error al conectar database: {e}")

    try:
        await database2.connect()
        app.state.db2_status = True
    except Exception as e:
        print(f"❌ Error al conectar database2: {e}")

# 🛑 Desconectar la base de datos cuando la API se detiene
@app.on_event("shutdown")
async def shutdown():
    if app.state.db1_status:
        await database.disconnect()
    
    if app.state.db2_status:
        await database2.disconnect()

# 🌐 Ruta de prueba para verificar la conexión
@app.get("/")
async def root():
    db1_status = app.state.db1_status
    db2_status = app.state.db2_status

    if db1_status and db2_status:
        return {"message": "✅ ¡Conexión exitosa a ambas bases de datos!"}
    elif db1_status:
        return {"message": "⚠️ Solo database está conectada. Error en database2."}
    elif db2_status:
        return {"message": "⚠️ Solo database2 está conectada. Error en database."}
    else:
        return {"message": "❌ Error: Ninguna base de datos se pudo conectar."}

@app.get('/prueba')
async def prueba():
    async with database.transaction():
        # Consulta para obtener los periodos
        periodos_query = "SELECT id, descripcion FROM periodo"
        periodos = await database.fetch_all(periodos_query)

        # Consulta para obtener las carreras
        carreras_query = "SELECT id, nombre_corto FROM carrera"
        carreras = await database.fetch_all(carreras_query)

        # Consulta optimizada para obtener los datos de aspirantes agrupados por periodo y carrera
        resultados_query = """
            SELECT 
                periodo_id,
                primera_opcion as carrera_id,
                COUNT(*) as total_aspirantes,
                SUM(CASE WHEN estado = 2 THEN 1 ELSE 0 END) as examinados,
                SUM(CASE WHEN estado = 3 THEN 1 ELSE 0 END) as admitidos,
                SUM(CASE WHEN estado = 4 THEN 1 ELSE 0 END) as no_admitidos
            FROM aspirante
            GROUP BY periodo_id, primera_opcion
        """
        resultados_db = await database.fetch_all(resultados_query)

        resultados = []

        # Procesar los resultados de la consulta
        for row in resultados_db:
            periodo_id = row["periodo_id"]
            carrera_id = row["carrera_id"]

            # Obtener descripciones de periodo y carrera
            periodo = next((p for p in periodos if p["id"] == periodo_id), None)
            carrera = next((c for c in carreras if c["id"] == carrera_id), None)

            if periodo and carrera:
                nombre_carrera = carrera["nombre_corto"].lower().capitalize()
                resultados.append({
                    "carrera": nombre_carrera,
                    "aspirantes": row["total_aspirantes"],
                    "examinados": row["examinados"],
                    "admitidos": row["admitidos"],
                    "no_admitidos": row["no_admitidos"],
                    "periodo": periodo["descripcion"]
                })

        return resultados