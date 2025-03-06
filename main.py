from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from database import engine
from sqlalchemy import text
from datetime import datetime, timedelta
from fastapi.middleware.cors import CORSMiddleware
from decouple import config
from itsdangerous import URLSafeTimedSerializer

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
@app.get('/')
def ingresos():
    return 'Hola mundo'


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



@app.get('/nuevosIngresos')
def nuevos_ingresos():
    resultados = []
    
    with engine.begin() as conn:
        # Obtener carreras
        carreras = conn.execute(
            text("SELECT id, nombre_oficial FROM carrera")
        ).mappings().fetchall()
        
        # Consulta principal
        resultados_query = conn.execute(text("""
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
            FROM aspirante AS asp
            JOIN persona AS per ON asp.persona_id = per.id
            LEFT JOIN matricula AS m ON m.persona_id = per.id
            JOIN periodo AS p ON p.id = asp.periodo_id
            GROUP BY asp.periodo_id, per.sexo, p.descripcion, asp.primera_opcion
        """)).mappings().fetchall()

    # Procesar resultados
    for row in resultados_query:
        carrera = next((c for c in carreras if c["id"] == row["carrera_id"]), None)
        sexo = "Masculino" if row["sexo"] == "M" else "Femenino"
        
        resultados.append({
            "admitidos": row["admitidos"],
            "carrera": carrera["nombre_oficial"] if carrera else "Desconocido",
            "inscritos": row["total_aspirantes"],
            "periodo": row["periodo"],
            "proceso": row["proceso"],
            "sexo": sexo,
            "total_ingresos": row["ingresados"]
        })
    
    return resultados


@app.get('/egresadostotales')
def egresadostotales():
    resultados = []
    
    with engine.begin() as conn:
        # Obtener carreras
        carreras = conn.execute(
            text("SELECT id, nombre_oficial, nombre_corto FROM carrera")
        ).mappings().fetchall()
        
        # Consulta principal
        resultados_query = conn.execute(text("""
            SELECT c.id as carrera, YEAR(e.fecha_titulacion) as anio,
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
            GROUP BY carrera, c.id, anio, periodo
        """)).mappings().fetchall()

    # Procesar resultados
    for row in resultados_query:
        carrera = next((c for c in carreras if c["id"] == row["carrera"]), None)
        nombre = carrera["nombre_corto"].lower().capitalize() if carrera and carrera["nombre_corto"] else carrera["nombre_oficial"] if carrera else "Desconocido"
        
        resultados.append({
            "carrera": nombre,
            "anio": row["anio"],
            "periodo": row["periodo"],
            "hombres": row["hombres"],
            "mujeres": row["mujeres"],
            "egresados": row["hombres"] + row["mujeres"]
        })
    
    return resultados



@app.get('/titulados')
def titulados():
    resultados = []
    
    with engine.begin() as conn:
        carreras = conn.execute(
            text("SELECT id, nombre_oficial, nombre_corto FROM carrera")
        ).mappings().fetchall()
        
        resultados_query = conn.execute(text("""
            SELECT 
                c.id AS carrera_id, 
                m.generacion,
                DATE(e.fecha_titulacion) AS fecha_titulacion,
                CASE 
                    WHEN MONTH(e.fecha_titulacion) BETWEEN 1 AND 4 THEN 'ENE-ABR'
                    WHEN MONTH(e.fecha_titulacion) BETWEEN 5 AND 8 THEN 'MAY-AGO'
                    WHEN MONTH(e.fecha_titulacion) BETWEEN 9 AND 12 THEN 'SEP-DIC'
                END AS cuatrimestre, 
                COUNT(e.id) AS total
            FROM egresado AS e
            LEFT JOIN matricula AS m ON e.matricula_id = m.id
            JOIN persona AS p ON m.persona_id = p.id
            JOIN plan_estudio AS pl ON pl.id = m.plan_estudio_id
            JOIN carrera AS c ON c.id = pl.carrera_id
            WHERE m.estado = 'E' 
                AND e.fecha_titulacion IS NOT NULL 
                AND e.estatus = 1
            GROUP BY c.id, m.generacion, e.fecha_titulacion, cuatrimestre
        """)).mappings().fetchall()

    for row in resultados_query:
        carrera = next((c for c in carreras if c["id"] == row["carrera_id"]), None)
        nombre = carrera["nombre_corto"].lower().capitalize() if carrera and carrera["nombre_corto"] else carrera["nombre_oficial"] if carrera else "Desconocido"
        
        fecha_raw = row["fecha_titulacion"]
        fecha_formateada = None
        
        if fecha_raw:
            try:
                fecha_obj = datetime.strptime(str(fecha_raw), "%Y-%m-%d")
                fecha_formateada = fecha_obj.strftime("%Y-%m-%d")
            except ValueError:
                fecha_formateada = "Fecha inválida"
        
        resultados.append({
            "carrera": nombre,
            "generacion": row["generacion"],
            "fecha_titulacion": fecha_formateada,
            "cuatrimestre_egreso": row["cuatrimestre"],
            "total": row["total"]
        })
    
    return resultados


@app.get('/transporte_solicitudes')
def transporte_solicitudes():
    resultados = []
    
    with engine.begin() as conn:
        # Obtener periodos
        periodos = conn.execute(
            text("SELECT id, descripcion FROM periodo")
        ).mappings().fetchall()
        
        # Consulta principal
        resultados_query = conn.execute(text("""
            SELECT 
                p.nombre_carrera, 
                p.periodo_id,
                COALESCE(
                    CASE 
                        WHEN p.concepto LIKE '%Nocturno%' THEN 'Nocturno'
                        WHEN p.concepto LIKE '%Matutino%' THEN 'Matutino'
                        WHEN p.concepto LIKE '%Vespertino%' THEN 'Vespertino'
                    END, 'Desconocido') AS turno,
                COALESCE(
                    CASE 
                        WHEN p.concepto LIKE '%LOMA - PROL. BERNARDO QUINTANA%' THEN 'Ruta 4'
                        WHEN p.concepto LIKE '%AV. DE LA LUZ VESPERTINO%' THEN 'Ruta 1'
                        WHEN p.concepto LIKE '%GOMEZ MORIN%' THEN 'Ruta 2'
                        WHEN p.concepto LIKE '%PASEO CONSTITUYENTES%' THEN 'Ruta 3'
                        WHEN p.concepto LIKE '%PIE DE LA CUESTA%' THEN 'Ruta 5'
                        WHEN p.concepto LIKE '%LIBRAMIENTO SUR PONIENTE%' THEN 'Ruta 6'
                    END, 'Desconocido') AS ruta,
                COUNT(CASE WHEN per.sexo = 'M' THEN 1 END) AS hombres,
                COUNT(CASE WHEN per.sexo = 'F' THEN 1 END) AS mujeres,
                COUNT(*) AS total
            FROM pago AS p
            LEFT JOIN persona AS per ON p.persona_id = per.id
            LEFT JOIN matricula AS m ON m.persona_id = per.id
            WHERE p.concepto LIKE '%CUOTA DE RECUPERACION%'
                AND p.concepto NOT LIKE '%(2 DE 3)%'
                AND p.concepto NOT LIKE '%(3 DE 3)%' 
            GROUP BY turno, ruta, p.periodo_id, p.nombre_carrera
        """)).mappings().fetchall()

    # Procesar resultados
    for row in resultados_query:
        periodo = next((p["descripcion"] for p in periodos if p["id"] == row["periodo_id"]), "Desconocido")
        
        resultados.append({
            "hombres": row["hombres"],
            "mujeres": row["mujeres"],
            "seleccionados": row["total"],
            "carrera": row["nombre_carrera"],
            "ruta": row["ruta"],
            "turno": row["turno"],
            "cuatrimestre": periodo
        })
    
    return resultados



@app.get('/rutas')
def rutas():
    resultados = []
    
    with engine.begin() as conn:
        # Obtener periodos
        periodos = conn.execute(
            text("SELECT id, descripcion FROM periodo")
        ).mappings().fetchall()
        
        # Consulta principal
        resultados_query = conn.execute(text("""
            SELECT 
                p.periodo_id,
                COALESCE(
                    CASE 
                        WHEN p.concepto LIKE '%Nocturno%' THEN 'Nocturno'
                        WHEN p.concepto LIKE '%Matutino%' THEN 'Matutino'
                        WHEN p.concepto LIKE '%Vespertino%' THEN 'Vespertino'
                    END, 'Desconocido') AS turno,
                COALESCE(
                    CASE 
                        WHEN p.concepto LIKE '%LOMA - PROL. BERNARDO QUINTANA%' THEN 'Ruta 4'
                        WHEN p.concepto LIKE '%AV. DE LA LUZ VESPERTINO%' THEN 'Ruta 1'
                        WHEN p.concepto LIKE '%GOMEZ MORIN%' THEN 'Ruta 2'
                        WHEN p.concepto LIKE '%PASEO CONSTITUYENTES%' THEN 'Ruta 3'
                        WHEN p.concepto LIKE '%PIE DE LA CUESTA%' THEN 'Ruta 5'
                        WHEN p.concepto LIKE '%LIBRAMIENTO SUR PONIENTE%' THEN 'Ruta 6'
                    END, 'Desconocido') AS ruta,
                COUNT(*) AS total
            FROM pago AS p
            LEFT JOIN persona AS per ON p.persona_id = per.id
            WHERE p.concepto LIKE '%CUOTA DE RECUPERACION MOVILIDAD COMPLETO%' 
                AND p.estatus = 3 
                AND p.concepto IS NOT NULL
                AND p.concepto NOT LIKE '%(2 DE 3)%'
                AND p.concepto NOT LIKE '%(3 DE 3)%'
            GROUP BY turno, ruta, p.periodo_id
            HAVING ruta != 'Desconocido' AND total > 0
        """)).mappings().fetchall()

    # Procesar resultados
    for row in resultados_query:
        periodo = next((p["descripcion"] for p in periodos if p["id"] == row["periodo_id"]), "Desconocido")
        disponibles = max(50 - row["total"], 0)
        
        resultados.append({
            "lugares_disp": disponibles,
            "pagados": row["total"],
            "ruta": row["ruta"],
            "turno": row["turno"],
            "cuatrimestre": periodo
        })
    
    return resultados