# Instalaciones necesarias:
# pip install fastapi uvicorn sqlalchemy asyncmy 
# pip install asyncmy
# pip install databases
# pip install aiomysql

from fastapi import FastAPI
from database import database
from sqlalchemy import select, Table, MetaData

app = FastAPI()

# 🚀 Conectar la base de datos cuando la API se inicia
@app.on_event("startup")
async def startup():
    app.state.db1_status = False


    try:
        await database.connect()
        app.state.db1_status = True
    except Exception as e:
        print(f"❌ Error al conectar database: {e}")

from fastapi import FastAPI


# Definir una ruta para la raíz (esto es para tener una referencia)
@app.get("/")
def read_root():
    return {"message": "¡Hola, Mundo!"}



# 🛑 Desconectar la base de datos cuando la API se detiene
@app.on_event("shutdown")
async def shutdown():
    if app.state.db1_status:
        await database.disconnect()
    



@app.get('/ingresos')
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

        i = 1

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
                    "id": i,
                    "carrera": nombre_carrera,
                    "aspirantes": row["total_aspirantes"],
                    "examinados": row["examinados"],
                    "no_admitidos": row["no_admitidos"],
                    "periodo": periodo["descripcion"]
                })
                i += 1

        return resultados

#ruta para reingresos/bajas

@app.get('/equivalencias')
async def prueba():
    async with database.transaction():
        #4,5,7,8,20


        pass

@app.get('/maestrias')
async def prueba():
    async with database.transaction():
        #15, 16, 17, 18


        pass

@app.get('/egresados')
async def prueba():
    async with database.transaction():
        #4,5,7,8,20


        pass


@app.get('/egresados_totales')
async def prueba():
    async with database.transaction():
        #4,5,7,8,20


        pass

@app.get('/titulados')
async def prueba():
    async with database.transaction():
        #4,5,7,8,20


        pass

@app.get('/transporte_solicitudes')
async def prueba():
    async with database.transaction():
        #4,5,7,8,20


        pass

@app.get('/rutas')
async def prueba():
    async with database.transaction():
        #4,5,7,8,20


        pass