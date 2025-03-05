# Instalaciones necesarias:
# pip install fastapi uvicorn sqlalchemy asyncmy 
# pip install asyncmy
# pip install databases
# pip install aiomysql

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi import Request
from datetime import datetime, timedelta
from database import database
from sqlalchemy import select, Table, MetaData
from fastapi.middleware.cors import CORSMiddleware
import redis
from itsdangerous import URLSafeTimedSerializer
from decouple import config
from security import (
    SECRET_KEY,
    ALGORITHM,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    oauth2_scheme,
    User,
    UserInDB,
    verify_password,
    get_password_hash,
    get_user,
    authenticate_user,
    create_access_token,
    fake_users_db,
    get_current_user,
    Token,
    TokenData,
)

app = FastAPI()

SECRET_KEY = config("SECRET_KEY")
serializer = URLSafeTimedSerializer(SECRET_KEY)

def generate_csrf_token():
    return serializer.dumps("csrf_token")

def validate_csrf_token(token: str):
    try:
        serializer.loads(token, max_age=3600)  # El token expira en 1 hora
        return True
    except:
        return False

app.add_middleware(
    CORSMiddleware,
    allow_headers=["*"],  # Permite "X-CSRF-Token"
)

@app.get("/get-csrf-token")
async def get_csrf_token():
    csrf_token = generate_csrf_token()
    return {"csrf_token": csrf_token}

@app.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(fake_users_db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


# 🚀 Conectar la base de datos cuando la API se inicia
@app.on_event("startup")
async def startup():
    app.state.db1_status = False
    try:
        await database.connect()
        app.state.db1_status = True
        print("Si hay conexion we uwu")
    except Exception as e:
        print(f"❌ Error al conectar database: {e}")

# 🛑 Desconectar la base de datos cuando la API se detiene
@app.on_event("shutdown")
async def shutdown():
    if app.state.db1_status:
        await database.disconnect()

# Definir una ruta para la raíz (esto es para tener una referencia)
@app.get("/")
def read_root():
    return {"message": "¡Hola, Mundo!"}

# Obtener periodos
async def get_periodos():
    return await database.fetch_all("SELECT id, descripcion FROM periodo")

# Obtener carreras
async def get_carreras():
    return await database.fetch_all("SELECT id, nombre_oficial, nombre_corto FROM carrera")

# Ruta protegida para obtener ingresos
@app.get('/ingresos')
async def prueba(current_user: User = Depends(get_current_user)):
    async with database.transaction():
        periodos = await get_periodos()
        carreras = await get_carreras()

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
async def prueba(current_user: User = Depends(get_current_user)):
    async with database.transaction():
    
        periodos = await get_periodos()
        carreras = await get_carreras()

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
async def prueba(current_user: User = Depends(get_current_user)):
    async with database.transaction():

        periodos = await get_periodos()

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
async def prueba(current_user: User = Depends(get_current_user)):
    async with database.transaction():


        carreras = await get_carreras()
        
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

@app.get('/egresadostotales')
async def prueba(current_user: User = Depends(get_current_user)):
    async with database.transaction():

        carreras = await get_carreras()
        
        # Consulta para obtener los egresados por periodo
        consulta = """
        SELECT c.id as carrera, YEAR(e.fecha_titulacion) as anio,
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
        GROUP BY carrera, c.id, anio, periodo;  -- Agrupa por periodo
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
                "anio": row["anio"],
                "periodo": row["periodo"],  # Usamos 'periodo' en lugar de 'cuatrimestre'
                "hombres": row["hombres"],
                "mujeres": row["mujeres"],
                "egresados": row["hombres"] + row["mujeres"]  # Calculamos el total de egresados
            })
        
        return resultados

@app.get('/nuevosIngresos')
async def nuevos_ingresos(current_user: User = Depends(get_current_user)):
    async with database.transaction():

        carreras = await get_carreras()

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


#Todavía no sabemos para que se utiliza.

@app.get('/egresados_totales')
async def prueba(current_user: User = Depends(get_current_user)):
    async with database.transaction():
        #4,5,7,8,20


        pass





@app.get('/titulados')
async def titulados(current_user: User = Depends(get_current_user)):
    async with database.transaction():
        # Consulta para obtener las carreras

        carreras = await get_carreras()

        # Consulta para obtener los egresados por periodo
        consulta = """
        SELECT 
            c.id AS carrera_id, 
            m.generacion,
            e.fecha_titulacion AS fecha_titulacion,
            CASE 
                WHEN MONTH(e.fecha_titulacion) BETWEEN 1 AND 4 THEN 'ENE-ABR'
                WHEN MONTH(e.fecha_titulacion) BETWEEN 5 AND 8 THEN 'MAY-AGO'
                WHEN MONTH(e.fecha_titulacion) BETWEEN 9 AND 12 THEN 'SEP-DIC'
            END AS cuatrimestre, 
            COUNT(e.id) AS total
        FROM 
            egresado AS e
        LEFT JOIN 
            matricula AS m ON e.matricula_id = m.id
        JOIN 
            persona AS p ON m.persona_id = p.id
        JOIN 
            plan_estudio AS pl ON pl.id = m.plan_estudio_id
        JOIN 
            carrera AS c ON c.id = pl.carrera_id
        WHERE 
            m.estado = 'E' 
            AND e.fecha_titulacion IS NOT NULL 
            AND e.estatus = 1
        GROUP BY 
            c.id, m.generacion, e.fecha_titulacion, cuatrimestre;
        """

        resultados_query = await database.fetch_all(consulta)

        # Construir la lista de resultados
        resultados = []
        for row in resultados_query:
            carrera_id = row["carrera_id"]
            
            # Buscar la carrera correspondiente en la lista de carreras
            carrera = next((c for c in carreras if c["id"] == carrera_id), None)
            nombre_carrera = carrera["nombre_oficial"] if carrera else "Carrera no encontrada"
            
            # Usar el nombre corto si está disponible
            if carrera and hasattr(carrera, "nombre_corto") and carrera["nombre_corto"]:
                nombre_carrera = carrera["nombre_corto"].lower().capitalize()
            
            resultados.append({
                "carrera": nombre_carrera,  # Nombre de la carrera formateado
                "generacion": row["generacion"],
                "fecha_titulacion": row["fecha_titulacion"],
                "cuatrimestre_egreso": row["cuatrimestre"],
                "total": row["total"]
            })
        
        return resultados





@app.get('/transporte_solicitudes')
async def prueba(current_user: User = Depends(get_current_user)):
    async with database.transaction():
        # Obtener los periodos

        periodos = await get_periodos()

        # Consulta principal
        consulta = """
        SELECT 
            p.nombre_carrera, 
            p.periodo_id,
            COALESCE(
                CASE 
                    WHEN p.concepto LIKE '%Nocturno%' THEN 'Nocturno'
                    WHEN p.concepto LIKE '%Matutino%' THEN 'Matutino'
                    WHEN p.concepto LIKE '%Vespertino%' THEN 'Vespertino'
                END, 
                'Desconocido'
            ) AS turno,
            COALESCE(
                CASE 
                    WHEN p.concepto LIKE '%LOMA - PROL. BERNARDO QUINTANA%' THEN 'Ruta 4'
                    WHEN p.concepto LIKE '%AV. DE LA LUZ VESPERTINO%' THEN 'Ruta 1'
                    WHEN p.concepto LIKE '%GOMEZ MORIN%' THEN 'Ruta 2'
                    WHEN p.concepto LIKE '%PASEO CONSTITUYENTES%' THEN 'Ruta 3'
                    WHEN p.concepto LIKE '%PIE DE LA CUESTA%' THEN 'Ruta 5'
                    WHEN p.concepto LIKE '%LIBRAMIENTO SUR PONIENTE%' THEN 'Ruta 6'
                END, 
                'Desconocido'
            ) AS ruta,
            COUNT(CASE WHEN per.sexo = 'M' THEN 1 END) AS hombres,
            COUNT(CASE WHEN per.sexo = 'F' THEN 1 END) AS mujeres,
            COUNT(*) AS total
        FROM 
            pago AS p
        LEFT JOIN 
            persona AS per ON p.persona_id = per.id
        LEFT JOIN 
            matricula AS m ON m.persona_id = per.id
        WHERE 
            p.concepto LIKE '%CUOTA DE RECUPERACION%'
            AND p.concepto NOT LIKE '%(2 DE 3)%'  -- Excluir pagos parciales
            AND p.concepto NOT LIKE '%(3 DE 3)%' 
        GROUP BY 
            turno, ruta, p.periodo_id, p.nombre_carrera;
        """

        # Ejecutar la consulta principal
        resultados_query = await database.fetch_all(consulta)

        # Procesar los resultados
        resultados = []
        for row in resultados_query:
            periodo_id = row["periodo_id"]
            # Buscar la descripción del período correspondiente
            periodo = next((p["descripcion"] for p in periodos if p["id"] == periodo_id), "Desconocido")

            resultados.append({
                "hombres": row["hombres"],
                "mujeres": row["mujeres"],
                "seleccionados": row["total"],
                "carrera": row["nombre_carrera"],  # Corregido: usar nombre_carrera en lugar de cuatrimestre
                "ruta": row["ruta"],
                "turno": row["turno"],
                "cuatrimestre": periodo  # Solo la descripción del período
            })
        
        return resultados


@app.get('/rutas')
async def rutas(current_user: User = Depends(get_current_user)):
    async with database.transaction():

        
        periodos = await get_periodos()

        # Consulta principal para obtener los resultados de las rutas
        consulta = """
        SELECT 
            p.periodo_id,
            COALESCE(
                CASE 
                    WHEN p.concepto LIKE '%Nocturno%' THEN 'Nocturno'
                    WHEN p.concepto LIKE '%Matutino%' THEN 'Matutino'
                    WHEN p.concepto LIKE '%Vespertino%' THEN 'Vespertino'
                END, 
                'Desconocido'
            ) AS turno,
            COALESCE(
                CASE 
                    WHEN p.concepto LIKE '%LOMA - PROL. BERNARDO QUINTANA%' THEN 'Ruta 4'
                    WHEN p.concepto LIKE '%AV. DE LA LUZ VESPERTINO%' THEN 'Ruta 1'
                    WHEN p.concepto LIKE '%GOMEZ MORIN%' THEN 'Ruta 2'
                    WHEN p.concepto LIKE '%PASEO CONSTITUYENTES%' THEN 'Ruta 3'
                    WHEN p.concepto LIKE '%PIE DE LA CUESTA%' THEN 'Ruta 5'
                    WHEN p.concepto LIKE '%LIBRAMIENTO SUR PONIENTE%' THEN 'Ruta 6'
                END, 
                'Desconocido'
            ) AS ruta,
            COUNT(*) AS total
        FROM 
            pago AS p
        LEFT JOIN 
            persona AS per ON p.persona_id = per.id
        WHERE 
            p.concepto LIKE '%CUOTA DE RECUPERACION MOVILIDAD COMPLETO%' 
            AND p.estatus = 3 
            AND p.concepto IS NOT NULL
            AND p.concepto NOT LIKE '%(2 DE 3)%'  -- Excluir pagos parciales
            AND p.concepto NOT LIKE '%(3 DE 3)%'  -- Excluir pagos parciales
        GROUP BY 
            turno, ruta, p.periodo_id
        HAVING 
            ruta != 'Desconocido' 
            AND total > 0;
        """

        resultados_query = await database.fetch_all(consulta)

        # Procesar los resultados
        resultados = []

        for row in resultados_query:
            periodo_id = row["periodo_id"]
            # Buscar la descripción del período correspondiente
            periodo = next((p["descripcion"] for p in periodos if p["id"] == periodo_id), "Desconocido")

            lugares_usados = row["total"]
            lugares_disponibles = max(50 - lugares_usados, 0)

            resultados.append({
                "lugares_disp": lugares_disponibles,
                "pagados": row["total"],
                "ruta": row["ruta"],
                "turno": row["turno"],
                "cuatrimestre": periodo  # Solo la descripción del período
            })
        
        return resultados