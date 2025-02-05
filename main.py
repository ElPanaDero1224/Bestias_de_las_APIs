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
    # Consulta para obtener los periodos
    periodos_query = "SELECT id, descripcion FROM periodo"
    periodos = await database.fetch_all(periodos_query)

    # Consulta para obtener las carreras
    carreras_query = "SELECT id, nombre_corto FROM carrera"
    carreras = await database.fetch_all(carreras_query)

    resultados = []

    for periodo in periodos:
        periodo_id = periodo["id"]
        desc_periodo = periodo["descripcion"]

        for carrera in carreras:
            carrera_id = carrera["id"]
            desc_carrera = carrera["nombre_corto"]

            # Consulta combinada para obtener todos los conteos en una sola consulta
            conteo_query = """
                SELECT 
                    SUM(CASE WHEN estado = 1 THEN 1 ELSE 0 END) as aspirantes_count,
                    SUM(CASE WHEN estado = 2 THEN 1 ELSE 0 END) as examinados_count,
                    SUM(CASE WHEN estado = 3 THEN 1 ELSE 0 END) as admitidos_count,
                    SUM(CASE WHEN estado = 4 THEN 1 ELSE 0 END) as no_admitidos_count
                FROM aspirante 
                WHERE periodo_id = :periodo_id 
                AND primera_opcion = :carrera_id
            """
            conteo = await database.fetch_one(conteo_query, {"periodo_id": periodo_id, "carrera_id": carrera_id})

            # Extraer los valores del conteo
            aspirantes_count = conteo["aspirantes_count"] or 0
            examinados_count = conteo["examinados_count"] or 0
            admitidos_count = conteo["admitidos_count"] or 0
            no_admitidos_count = conteo["no_admitidos_count"] or 0

            # Verificar la condición
            if aspirantes_count != 0 and examinados_count != 0 and admitidos_count != 0 and no_admitidos_count == 0:
                # Agregar el resultado a la lista
                resultados.append({
                    "carrera": desc_carrera,
                    "aspirantes": aspirantes_count,
                    "examinados": examinados_count,
                    "admitidos": admitidos_count,
                    "no_admitidos": no_admitidos_count,
                    "periodo": desc_periodo
                })

    # Retornar los resultados después de procesar todos los periodos y carreras
    return resultados