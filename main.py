from fastapi import FastAPI
from database import engine
from sqlalchemy import text

app = FastAPI()

# 🚀 Evento de inicio
@app.on_event("startup")
def startup():
    app.state.db1_status = False
    try:
        # Prueba de conexión
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        app.state.db1_status = True
        print("✅ Conexión exitosa a MySQL 5.1")
    except Exception as e:
        print(f"❌ Error de conexión: {str(e)}")

# Ruta de prueba modificada
@app.get('/ingresos')
def ingresos():
    resultados = []
    with engine.begin() as conn:  # Transacción síncrona
        # Consulta periodos
        periodos = conn.execute(text("SELECT id, descripcion FROM periodo")).fetchall()
        
        # Consulta carreras
        carreras = conn.execute(text("SELECT id, nombre_corto FROM carrera")).fetchall()
        
        # Consulta principal
        resultados_db = conn.execute(text("""
            SELECT 
                periodo_id,
                primera_opcion as carrera_id,
                COUNT(*) as total_aspirantes,
                SUM(CASE WHEN estado = 2 THEN 1 ELSE 0 END) as examinados,
                SUM(CASE WHEN estado = 3 THEN 1 ELSE 0 END) as admitidos,
                SUM(CASE WHEN estado = 4 THEN 1 ELSE 0 END) as no_admitidos
            FROM aspirante
            GROUP BY periodo_id, primera_opcion
        """)).fetchall()

    # Procesamiento de datos
    i = 1
    for row in resultados_db:
        periodo = next((p for p in periodos if p[0] == row[0]), None)
        carrera = next((c for c in carreras if c[0] == row[1]), None)
        
        if periodo and carrera:
            resultados.append({
                "id": i,
                "carrera": carrera[1].lower().capitalize(),
                "aspirantes": row[2],
                "examinados": row[3],
                "no_admitidos": row[5],  # Ajustado al índice correcto
                "periodo": periodo[1]
            })
            i += 1

    return resultados


@app.get('/equivalencias')
def equivalencias():
    resultados = []
    
    with engine.begin() as conn:  # Transacción síncrona
        # Consultar periodos
        periodos = conn.execute(text("SELECT id, descripcion FROM periodo")).fetchall()
        
        # Consultar carreras
        carreras = conn.execute(text("SELECT id, nombre_corto FROM carrera")).fetchall()
        
        # Consulta principal
        resultados_db = conn.execute(text("""
            SELECT 
                periodo_id,
                nombre_carrera as carrera,
                COUNT(*) as total_aspirantes,
                SUM(CASE WHEN estatus = 3 THEN 1 ELSE 0 END) as examinados,
                SUM(CASE WHEN estatus = 1 THEN 1 ELSE 0 END) as no_admitidos
            FROM pago
            WHERE concepto = 'EQUIVALENCIA, REVALIDACION O TRANSFERENCIA'
            GROUP BY periodo_id, carrera
        """)).fetchall()

    # Procesamiento de datos
    i = 1
    for row in resultados_db:
        # Los índices ahora son posicionales: row[0] = periodo_id, row[1] = carrera, etc.
        periodo = next((p for p in periodos if p[0] == row[0]), None)
        carrera = next((c for c in carreras if c[1] == row[1]), None)  # Buscar por nombre_corto

        if periodo and carrera:
            resultados.append({
                "id": i,
                "carrera": row[1].lower().capitalize(),  # Usamos directamente el nombre del query
                "aspirantes": row[2],
                "examinados": row[3],
                "no_admitidos": row[4],
                "periodo": periodo[1]  # periodo[1] = descripcion
            })
            i += 1

    return resultados


@app.get('/maestrias')
def maestrias():
    resultados = []
    
    with engine.begin() as conn:  # Transacción síncrona
        # Consultar periodos
        periodos = conn.execute(text("SELECT id, descripcion FROM periodo")).mappings().fetchall()
        
        # Consultar carreras de maestría
        carreras = conn.execute(
            text("SELECT id, nombre_oficial FROM carrera WHERE nombre_oficial LIKE '%maestria%'")
        ).mappings().fetchall()
        
        # Consulta principal
        resultados_db = conn.execute(text("""
            SELECT 
                periodo_id,
                primera_opcion as carrera_id,
                COUNT(*) as total_aspirantes,
                SUM(CASE WHEN estado = 2 THEN 1 ELSE 0 END) as examinados,
                SUM(CASE WHEN estado = 3 THEN 1 ELSE 0 END) as admitidos,
                SUM(CASE WHEN estado = 4 THEN 1 ELSE 0 END) as no_admitidos
            FROM aspirante
            GROUP BY periodo_id, primera_opcion
        """)).mappings().fetchall()

    # Procesamiento de datos
    i = 1
    for row in resultados_db:
        # Buscar relaciones usando diccionarios
        periodo = next((p for p in periodos if p["id"] == row["periodo_id"]), None)
        carrera = next((c for c in carreras if c["id"] == row["carrera_id"]), None)

        if periodo and carrera:
            resultados.append({
                "id": i,
                "carrera": carrera["nombre_oficial"].lower().capitalize(),
                "aspirantes": row["total_aspirantes"],
                "examinados": row["examinados"],
                "no_admitidos": row["no_admitidos"],
                "periodo": periodo["descripcion"]
            })
            i += 1

    return resultados




@app.get('/egresados')
def egresados():
    resultados = []
    
    with engine.begin() as conn:  # Transacción síncrona
        # Consultar carreras
        carreras = conn.execute(
            text("SELECT id, nombre_oficial, nombre_corto FROM carrera")
        ).mappings().fetchall()
        
        # Consulta principal de egresados
        consulta = """
            SELECT 
                c.id as carrera, 
                m.generacion,
                YEAR(e.fecha_titulacion) as anio,
                CASE 
                    WHEN MONTH(e.fecha_titulacion) BETWEEN 1 AND 4 THEN 'ENE-ABR'
                    WHEN MONTH(e.fecha_titulacion) BETWEEN 5 AND 8 THEN 'MAY-AGO'
                    WHEN MONTH(e.fecha_titulacion) BETWEEN 9 AND 12 THEN 'SEP-DIC'
                END AS periodo,
                SUM(CASE WHEN p.sexo = 'F' THEN 1 ELSE 0 END) AS mujeres,
                SUM(CASE WHEN p.sexo = 'M' THEN 1 ELSE 0 END) AS hombres
            FROM egresado AS e
            LEFT JOIN matricula AS m ON e.matricula_id = m.id
            JOIN persona AS p ON m.persona_id = p.id
            JOIN plan_estudio AS pl ON pl.id = m.plan_estudio_id
            JOIN carrera AS c ON c.id = pl.carrera_id
            WHERE m.estado = 'E' AND e.fecha_titulacion IS NOT NULL
            GROUP BY carrera, m.generacion, c.id, anio, periodo
        """
        resultados_query = conn.execute(text(consulta)).mappings().fetchall()

    # Procesar resultados
    for row in resultados_query:
        carrera = next((c for c in carreras if c["id"] == row["carrera"]), None)
        
        nombre_carrera = carrera['nombre_oficial'] if carrera else "Carrera no encontrada"
        if carrera and carrera.get('nombre_corto'):
            nombre_carrera = carrera['nombre_corto'].lower().capitalize()

        resultados.append({
            "carrera": nombre_carrera,
            "generacion": row["generacion"],
            "año_egreso": row["anio"],
            "cuatrimestre": row["periodo"],
            "hombres": row["hombres"],
            "mujeres": row["mujeres"],
            "egresados": row["hombres"] + row["mujeres"]
        })

    return resultados