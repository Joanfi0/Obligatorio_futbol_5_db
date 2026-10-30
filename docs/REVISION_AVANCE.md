# Revisión del avance — 30/10/2026

## Conclusión


## Contraste con la consigna

| Área | Estado observado |
|---|---|
| Jugadores | Alta, modificación y baja; validación HTML, Python y restricciones SQL. Baja impedida por referencias. |
| Equipos y planteles | Tablas y datos; falta ABM y controlar 5–10 jugadores, máximo 2 docentes/funcionarios, misma facultad, capitán del plantel y cambios solo en inscripción. Un equipo por jugador/edición sí se protege mediante UNIQUE. |
| Complejos y canchas | Tablas y datos; falta ABM. |
| Partidos | Consulta; claves compuestas protegen pertenencia a edición y CHECK impide jugar contra sí mismo. Falta ABM, mínimo de jugadores, rivales repetidos, conflictos de cancha/turno y equipo/fecha. |
| Planillas, goles y tarjetas | Tablas y datos; FK exige planilla para gol/tarjeta. Falta interfaz y controlar equipo del partido, pertenencia al plantel y suspensiones. |
| Resultados | Vistas derivan marcador y posiciones, incluyendo autogoles. Falta controlar fin del turno y límite de corrección de 48 horas. Hay trigger contra eliminación de partido jugado, pero no constituye por sí solo una protección completa ante cambios de estado. |
| Sanciones | Datos de ejemplo y reportes; falta ABM y generación automática por roja/3 amarillas. |
| Usuarios DB | Separados para autenticación, administrador y planillero. Planillero solo consulta fixture en este avance; todavía no registra planillas. |
| Reportes | Nueve categorías solicitadas y tres extras. Algunas interpretaciones requieren documentarse (ver abajo). |
| Datos | Las pruebas comprueban 6 equipos, 9 partidos jugados en 3 fechas, planteles, capitanes y coherencia de planillas/sanciones del conjunto de muestra. |

Los datos correctos de ejemplo no demuestran que la aplicación impida cargar otros datos incorrectos. Es especialmente relevante para las reglas deportivas todavía pendientes.

## Relación con los materiales aportados

- **BD1_MR_SQL.pdf:** el ABM usa INSERT, UPDATE y DELETE; los reportes usan SELECT, WHERE, GROUP BY, ORDER BY, agregaciones y NOT EXISTS, acordes al material.
- **JOIN en SQL.pdf:** los JOIN unen jugadores, equipos y eventos; LEFT JOIN conserva equipos sin eventos en posiciones/fair play. No hace falta agregar todos los tipos de JOIN solo para mostrar que se conocen.
- **Seguridad 2024(1).pdf:** consultas parametrizadas, control de roles en backend y GRANT diferenciados son coherentes con lo enseñado. Aunque el material menciona ORM como alternativa, la consigna prohíbe usarlo y el proyecto respeta esa prohibición.
- Hay recursos que exceden lo desarrollado en esos materiales: triggers, vistas, CASE/COALESCE, GROUPING con ROLLUP, funciones de ventana OVER(), PBKDF2 y CSRF. No son por ello incorrectos ni están prohibidos, pero el equipo debe poder explicarlos. No se sustituyeron automáticamente consultas funcionales.

## Puntos a aclarar antes de la entrega final

1. El reporte de jugadores cuenta inscriptos por edición, no todos los jugadores registrados. La letra dice cantidad por facultad/tipo sin precisar ese filtro: documentar o consultar esa interpretación.
2. Uso de canchas/turnos agrupa cada combinación; no produce dos rankings independientes de canchas y turnos. Confirmar qué presentación esperan.
3. El porcentaje de estados incluye programados en el denominador. Está documentado; confirmar si quieren además comparar exclusivamente jugados frente a postergados/cancelados.
4. Los permisos de administrador todavía están limitados al ABM de jugadores; ampliarlos al implementar operaciones validadas, no declarar la gestión completa como realizada.
5. Completar autores, bitácora real y bibliografía del informe. Las limitaciones de pruebas anteriores son históricas, no evidencia de cómo funciona actualmente en la PC del equipo.

## Cambios aplicados

- CSS separado por selectores y propiedades, con sangría.
- Las seis plantillas HTML/Jinja separadas en líneas y bloques.
- Python formateado para evitar sentencias amontonadas en una línea.
- run_local.py busca .env junto al script, independientemente de la carpeta de la terminal.
- README: nombre real de carpeta y eliminación del comando incompleto de pip en el arranque Docker.
- Informe: corregida afirmación sobre tildes en valores de dominio.

Se conserva el alcance del avance y las consultas existentes. No se implementaron los módulos pendientes ni se modificaron las credenciales.

## Validación de esta revisión

Se ejecutaron las 9 pruebas portables del proyecto. Son comprobaciones de dominio y datos, con SQLite como oráculo parcial; no validan instalación MySQL, triggers, permisos ni concurrencia. La consulta GROUPING/ROLLUP queda excluida por el propio conjunto de pruebas. No se dispone de Docker en este entorno para afirmar una validación integral contra MySQL.

## Corrección de datos y consulta de equipos

Se reemplazaron los 36 nombres de muestra por nombres y apellidos ficticios realistas. Se agregó consulta de equipos/planteles para administrador por edición y una columna de inscripciones en Jugadores. El ABM de equipos sigue pendiente. Para bases existentes ver docs/ACTUALIZAR_NOMBRES.md (ACTUALIZAR_NOMBRES.md desde esta carpeta). Pasaron las 9 pruebas y comprobaciones de rutas/consultas con SQLite; no se ejecutó integración MySQL.
