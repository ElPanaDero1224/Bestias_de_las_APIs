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