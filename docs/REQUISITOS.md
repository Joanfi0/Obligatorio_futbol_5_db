# Matriz de alcance contra la consigna

Fuente: Obligatorio BD - Segundo Semestre 2026.pdf, páginas 1–4. Esta matriz distingue código incluido de funcionalidades aún pendientes; nada de lo pendiente se considera cumplido por una nota o por datos de ejemplo.

| Requisito | Estado en el avance | Ubicación / siguiente paso |
|---|---|---|
| Python, MySQL, sin ORM | Implementado; integración pendiente de ejecutar | app/, sql/, requirements.txt |
| 14 tablas mínimas | Implementado | sql/01_esquema.sql |
| Datos maestros, 6 equipos y 3 fechas jugadas | Incluidos y coherencia probada | sql/03_datos.sql |
| Login y dos roles | Implementado; ejecución HTTP pendiente | app/web.py, sql/04 |
| Seguridad en DB | Grants mínimos implementados | Administrador: lectura + ABM jugadores; planillero: fixture de lectura. Falta completar permisos de módulos futuros |
| ABM jugadores | Implementado con validaciones en formulario, Python y DB | CI inmutable; baja referenciada rechazada |
| ABM equipos y planteles | Pendiente | Tablas y datos iniciales disponibles |
| Plantel de 5–10, misma facultad, máximo 2 docentes/funcionarios | Datos iniciales cumplen; reglas de escritura pendientes | Validar al activar torneo y en cambios de plantel bajo bloqueo |
| Capitán dentro del plantel | Datos iniciales cumplen; enforcement pendiente | FK actual confirma existencia del jugador, no pertenencia al equipo |
| Una persona en un equipo por edición | Implementado en DB | UNIQUE(ci_jugador,id_torneo) |
| Planteles editables solo en inscripción | Pendiente | No hay endpoint de modificación de planteles |
| ABM complejos y canchas | Pendiente | Tablas y semillas incluidas |
| Turnos entre 18 y 23 de una hora | Implementado en DB | CHECKs y cinco turnos maestros |
| ABM partidos / generación fixture | Pendiente | Solo consulta de fixture predefinido |
| Equipos de misma edición y distintos | Implementado en DB | FK compuesta y CHECK |
| Mínimo 5 jugadores para programar | Pendiente | Procedimiento transaccional |
| Rival único salvo cancelado | Pendiente | Datos iniciales cumplen; falta garantizar concurrencia |
| Equipo una vez por fecha | Pendiente | Tabla auxiliar de ocupaciones propuesta |
| Sin superposición cancha/día/turno | Pendiente | Tabla auxiliar de ocupaciones propuesta |
| Planillas, goles y tarjetas | Modelo y muestra; interfaz de carga pendiente | Tablas base y relaciones |
| Participantes del plantel/equipos y no suspendidos | Datos iniciales comprobados; validación de escritura pendiente | No hay permisos de escritura ni endpoints todavía |
| Solo participantes pueden recibir goles/tarjetas | Implementado en DB | FK a planilla_partido(id_partido,ci_jugador) |
| Resultado calculado de goles, incluidos autogoles | Implementado como vistas | sql/02_vistas.sql; oráculo probado |
| Marcar jugado solo después del fin del turno | Pendiente | Evaluar fin del turno en America/Montevideo |
| No borrar partido jugado | Implementado con trigger | Además, FK conserva referencias |
| Correcciones dentro de 48 horas | Pendiente | Fecha de disputa = día + hora_fin, no momento de carga |
| Puntos 3/1/0 y desempates | Implementado | Reporte posiciones |
| Sanción automática roja / 3 amarillas | Pendiente | Las sanciones iniciales se cargan explícitamente, no se generan solas |
| Sanción disciplinaria por varias fechas | Modelo y ejemplo; ABM pendiente | Rango inclusivo inicio a inicio+cantidad−1 |
| Planillero solo registra datos de juego | Acceso restringido; función de registro pendiente | No puede administrar jugadores ni reportes; fixture de apoyo |
| Nueve reportes solicitados | Consultas y pantallas implementadas; MySQL pendiente | app/reports.json |
| Tres consultas adicionales | Implementadas | Defensa, rangos de sanción y composición de planteles |
| Instructivo local | Incluido | README.md |
| Informe, decisiones, mejoras, bitácora, bibliografía | Borrador incluido | docs/INFORME.md |
| GitHub público | Pendiente del estudiante | No se creó ni publicó un repositorio |
| Docker y Compose | Configuración incluida y validada estáticamente | Ejecución pendiente |
| Aplicación funcional completa | NO cumplido aún | Este paquete es un avance, no la entrega final |

## Orden recomendado de implementación

1. Arrancar MySQL, ejecutar las pruebas de integración y registrar resultados.
2. Agregar ABM complejos/canchas y edición de torneos.
3. Planteles y capitanía con una transacción por operación: bloquear torneo/equipo, validar etapa, facultad, límite de jugadores y cupo docente/funcionario. Permitir plantel incompleto durante el armado; exigir 5–10 al habilitar el equipo. Este criterio requiere confirmación docente.
4. Programación: reservar ocupaciones mediante índices únicos en tablas auxiliares, dentro de la misma transacción que crea el partido. Liberarlas al cancelar; definir si postergado conserva reserva. La simple consulta SELECT seguida de INSERT sin bloqueo no evita carreras.
5. Carga de planillas y eventos con procedimientos controlados y permisos EXECUTE por rol.
6. Cierre y corrección de partido: comprobar tiempo, recalcular sanciones afectadas y auditar cambios. Probar modificaciones simultáneas.
7. Revisar las 12 consultas con casos vacíos, empates y autogoles; comprobar toda la aplicación desde ambos roles.

## Preguntas concretas para el docente

- ¿Las amarillas generan otra sanción al llegar a 6, 9, etc., o solo al alcanzar las primeras 3? ¿Se reinicia el contador al sancionar?
- ¿Qué sucede al corregir tarjetas si ya hay partidos posteriores cargados? ¿Cómo se corrigen sanciones derivadas?
- ¿Sanciones simultáneas se superponen o se cumplen consecutivamente?
- ¿Un partido postergado libera cancha y turno? ¿Puede conservar la fecha de torneo al reprogramarse?
- ¿Qué rango de minutos de gol se admite? El avance asume 0–60, por la duración del turno, pendiente de confirmación.
- ¿Se pueden cambiar facultad/tipo de un jugador entre ediciones? El avance bloquea cambios si existe cualquier inscripción para preservar el historial.
