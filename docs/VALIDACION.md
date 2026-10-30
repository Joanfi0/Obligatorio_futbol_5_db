# Validación del avance

## Ejecutado el 30/10/2026

| Comprobación | Resultado |
|---|---|
| `python -m unittest discover -s tests -v` | 9 pruebas aprobadas |
| `python -m compileall -q app run_local.py tests` | Sin errores de sintaxis |
| `docker compose --env-file .env.example config --quiet` | Configuración válida |
| Disponibilidad del motor Docker | No disponible: motor Linux de Docker Desktop no iniciado |
| Instalación de Flask y MySQL Connector | No realizada: resolución de pypi.org falló en el entorno |
| Arranque MySQL, scripts de instalación, permisos efectivos | No ejecutado |
| Recorrido HTTP/navegador | No ejecutado |

Las nueve pruebas verifican: jugador válido, rechazo de datos inválidos, seis equipos/tres fechas, planteles/capitanía/cupo de personal, calendario sin cruces, planillas compatibles y suspensiones, balance de posiciones, autogol para el rival, once consultas portables y seis jugadores sin participación.

El motor SQLite usado por el oráculo de pruebas no es la base de la aplicación. No verifica claves, triggers, permisos ni dialecto de MySQL. La consulta de promedios con GROUPING/WITH ROLLUP debe verificarse en MySQL.

## Comprobaciones que debe ejecutar el equipo al iniciar Docker

1. Seguir README y confirmar que ambos servicios arrancan y los logs no muestran fallos de SQL.
2. Ingresar como administrador. Abrir los doce reportes en la edición 2025; revisar también la edición vacía 2026.
3. Confirmar en posiciones: seis equipos, tres partidos jugados por equipo, nueve partidos en total; suma de goles a favor igual a goles en contra.
4. Resultado del partido 1: local 3, visitante 1. El autogol no debe sumar al goleador.
5. Reporte sin participación: seis jugadores (la camiseta 6 de cada equipo).
6. Crear un jugador nuevo, editar su nombre y eliminarlo. Verificar rechazo de CI/email repetidos, fecha futura y facultad inexistente.
7. Intentar borrar un jugador inscripto: debe rechazarse. Intentar cambiar tipo/facultad de un inscripto: debe rechazarse.
8. Ingresar como planillero: fixture permitido; `/jugadores` y `/reportes/posiciones` deben responder 403. Un POST sin token CSRF debe rechazarse.
9. Confirmar los grants desde el cliente MySQL. El planillero no debe poder insertar jugadores, leer `login` ni modificar partidos.
10. Documentar versión de MySQL, comandos, salidas y capturas reales. No marcar estos pasos como aprobados antes de ejecutarlos.

## Pruebas para agregar junto a funcionalidades pendientes

- Dos altas simultáneas para la misma cancha/turno o equipo/fecha: solo una debe confirmar.
- Equipo contra sí mismo, rival repetido, distinta edición, plantel inválido.
- Cambio de plantel fuera de inscripción y capitán externo al plantel.
- Planilla con jugador ajeno/suspendido; eventos de jugador ausente de la planilla.
- Cierre antes del fin del turno; corrección después de 48 horas.
- Roja y tercera amarilla crean sanción de próxima fecha sin duplicarla; correcciones recalculan efectos.
- Usuarios planilleros no pueden eludir validaciones escribiendo directamente en DB.
