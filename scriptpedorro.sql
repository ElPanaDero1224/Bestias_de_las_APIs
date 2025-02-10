use sistemaintegral;
select * from matricula INNER JOIN plan_estudio;
select * from aspirante;
select * from persona ;
select * from matricula where matricula='122043308';
select * from inscripcion;
select * from control_ficha_maestria;
SELECT * FROM inscripcion where tipo_inscripcion_id=7;

-- Intento de reinscripciones
SELECT * FROM pago_transporte;

SELECT * from persona where id=35182;
SELECT * from carrera;
SELECT * from inscripcion;
SELECT * from tipo_inscripcion;
SELECT * from periodo where id=3;
SELECT * from matricula WHERE matricula='122043301';
SELECT * from aspirante_dictamen_comentario;
SELECT * from convocatoria;
SELECT * from inscripcion WHERE matricula_id=14791;
SELECT * from baja where matricula_id=14791;
SELECT * from plan_estudio;

SELECT * from aspirante;
SELECT * from baja;

SELECT count(distinct cuatrimestre) from inscripcion;
SELECT MAX(cuatrimestre) AS max_cuatrimestre FROM inscripcion;

SELECT inscripcion.cuatrimestre FROM inscripcion left join baja on baja.matricula_id = inscripcion.matricula_id;

SELECT * from matricula where matricula=123047236;
SELECT * from persona where nombre='Rogelio Ernesto';
-- 27383 38856
SELECT * from pago where persona_id=38856;

SELECT * 
FROM pago 
WHERE nombre_carrera LIKE '%maestria%';

SELECT * FROM carrera WHERE nombre_corto LIKE '%maestria%';

SELECT * FROM aspirante where primera_opcion=11;

SELECT id, nombre_oficial FROM carrera WHERE nombre_oficial LIKE '%maestria%'

SELECT * FROM matricula;

select * from plan_estudio;

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
GROUP BY carrera, m.generacion, c.id, anio, cuatrimestre;  -- Agrupa por periodo

SELECT *
FROM egresado;


SELECT * FROM periodo;
