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
        # Consulta para obtener los periodos
        periodos_query = "SELECT id, descripcion FROM periodo"
        periodos = await database.fetch_all(periodos_query)

        # Consulta para obtener las carreras
        carreras_query = "SELECT nombre_corto FROM carrera"
        carreras = await database.fetch_all(carreras_query)

        # Consulta principal para obtener los datos de los pagos
        resultado_query = """
            SELECT 
                periodo_id,
                nombre_carrera as carrera,
                COUNT(*) as total_aspirantes,
                SUM(CASE WHEN estatus = 3 THEN 1 ELSE 0 END) as examinados,
                SUM(CASE WHEN estatus = 1 THEN 1 ELSE 0 END) as no_admitidos
            FROM pago
            WHERE concepto = 'EQUIVALENCIA, REVALIDACION O TRANSFERENCIA'
            GROUP BY periodo_id, carrera
        """
        resultados_db = await database.fetch_all(resultado_query)

        resultados = []
        i = 1

        for row in resultados_db:
            periodo_id = row["periodo_id"]
            carrera = row["carrera"]

            # Obtener descripciones de periodo y carrera
            periodo = next((p for p in periodos if p["id"] == periodo_id), None)
            carrera = next((c for c in carreras if c["nombre_corto"] == carrera), None)

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

@app.get('/maestrias')
async def prueba():
    async with database.transaction():
         # Consulta para obtener los periodos
        periodos_query = "SELECT id, descripcion FROM periodo"
        periodos = await database.fetch_all(periodos_query)

        # Consulta para obtener las carreras
        carreras_query = "SELECT id, nombre_oficial FROM carrera WHERE nombre_oficial LIKE '%maestria%'"
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
                nombre_carrera = carrera["nombre_oficial"].lower().capitalize()
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
        
        


        pass
#carreras_query = "SELECT id, nombre_oficial FROM carrera WHERE nombre_oficial LIKE '%maestria%'"

@app.get('/egresados')
async def prueba():
    async with database.transaction():
        # Consulta para obtener las carreras (incluyendo nombre_corto si es necesario)
        carreras_query = "SELECT id, nombre_oficial, nombre_corto FROM carrera"  # Asegúrate de incluir nombre_corto
        carreras = await database.fetch_all(carreras_query)
        
        # Consulta para obtener los egresados por periodo
        consulta = """
            SELECT 
                c.id as carrera, 
                m.generacion,
                YEAR(e.fecha_titulacion) as anio,
                CASE 
                    WHEN MONTH(e.fecha_titulacion) BETWEEN 1 AND 4 THEN 'ENE-ABR'
                    WHEN MONTH(e.fecha_titulacion) BETWEEN 5 AND 8 THEN 'MAY-AGO'
                    WHEN MONTH(e.fecha_titulacion) BETWEEN 9 AND 12 THEN 'SEP-DIC'
                END AS periodo,  -- Nombre del periodo
                SUM(CASE WHEN p.sexo = 'F' THEN 1 ELSE 0 END) AS mujeres,
                SUM(CASE WHEN p.sexo = 'M' THEN 1 ELSE 0 END) AS hombres
            FROM egresado AS e
            LEFT JOIN matricula AS m ON e.matricula_id = m.id
            JOIN persona AS p ON m.persona_id = p.id
            JOIN plan_estudio AS pl ON pl.id = m.plan_estudio_id
            JOIN carrera AS c ON c.id = pl.carrera_id
            WHERE m.estado = 'E' AND e.fecha_titulacion IS NOT NULL
            GROUP BY carrera, m.generacion, c.id, anio, periodo;  -- Agrupa por periodo
        """
        resultados_query = await database.fetch_all(consulta)
        
        # Construir la lista de resultados
        resultados = []
        for row in resultados_query:
            carrera_id = row["carrera"]  # Usamos "carrera" en lugar de "carrera_id"
            
            # Buscar la carrera correspondiente en la lista de carreras
            carrera = next((c for c in carreras if c["id"] == carrera_id), None)
            nombre_carrera = carrera['nombre_oficial'] if carrera else "Carrera no encontrada"
            
            # Formatear el nombre de la carrera (si es necesario)
            if carrera and 'nombre_corto' in carrera and carrera['nombre_corto']:
                nombre_carrera = carrera['nombre_corto'].lower().capitalize()
            
            resultados.append({
                "carrera": nombre_carrera,  # Usamos el nombre formateado de la carrera
                "generacion": row["generacion"],
                "año_egreso": row["anio"],
                "cuatrimestre": row["periodo"],  # Usamos 'periodo' en lugar de 'cuatrimestre'
                "hombres": row["hombres"],
                "mujeres": row["mujeres"],
                "egresados": row["hombres"] + row["mujeres"]  # Calculamos el total de egresados
            })
        
        return resultados

@app.get('/nuevosIngresos')
async def nuevos_ingresos():
    async with database.transaction():
        # Consulta para obtener las carreras
        carreras_query = "SELECT id, nombre_oficial, nombre_corto FROM carrera"
        carreras = await database.fetch_all(carreras_query)


        # Consulta principal para obtener los datos de los aspirantes
        consulta = """
        SELECT 
            asp.primera_opcion as carrera_id,
            asp.periodo_id AS IDperiodo,
            per.sexo,
            p.descripcion AS periodo,
            SUM(CASE WHEN m.matricula IS NOT NULL THEN 1 ELSE 0 END) AS ingresados,
            COUNT(asp.id) AS total_aspirantes,
            SUM(CASE WHEN asp.estado = 3 THEN 1 ELSE 0 END) AS admitidos,
            CASE
                WHEN p.descripcion LIKE '%PRIMER%' THEN '1er Proceso'
                WHEN p.descripcion LIKE '%SEGUNDA%' THEN '2do Proceso'
                WHEN p.descripcion LIKE '%TERCER%' THEN '3er Proceso'
                WHEN p.descripcion LIKE '%CUARTA%' THEN '4to Proceso'
                ELSE '1er Proceso'
            END AS proceso
        FROM 
            aspirante AS asp
        JOIN 
            persona AS per ON asp.persona_id = per.id
        LEFT JOIN 
            matricula AS m ON m.persona_id = per.id
        JOIN 
            periodo AS p ON p.id = asp.periodo_id
        GROUP BY 
            asp.periodo_id, per.sexo, p.descripcion, asp.primera_opcion;
        """

        resultados_query = await database.fetch_all(consulta)

        # Procesar los resultados
        resultados = []
        for row in resultados_query:
            sexo = "Masculino" if row["sexo"] == "M" else "Femenino"

            # Obtener el nombre de la carrera
            carrera = next((c for c in carreras if c["id"] == row["carrera_id"]), None)
            nombre_carrera = carrera["nombre_oficial"] if carrera else "Desconocido"

            resultados.append({
                "admitidos": row["admitidos"],
                "carrera": nombre_carrera,
                "inscritos": row["total_aspirantes"],
                "periodo": row["periodo"],
                "proceso": row["proceso"],  # Usamos la columna 'proceso' calculada en la consulta
                "sexo": sexo,
                "total_ingresos": row["ingresados"]
            })

        return resultados


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