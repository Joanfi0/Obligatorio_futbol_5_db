# Informe inicial — Torneo Interfacultades

Autores: **completar con integrantes reales**. Fecha del avance: 30/10/2026.

## Problema y alcance

El proyecto busca centralizar equipos, jugadores, canchas, calendario, resultados y sanciones del torneo. Este primer avance proporciona la estructura relacional, los datos de muestra, autenticación, administración de jugadores y reportes. La matriz REQUISITOS.md identifica cada funcionalidad todavía pendiente.

## Decisiones de implementación

- Python/Flask para una aplicación pequeña con páginas renderizadas en servidor. No se requiere framework JavaScript ni proceso de compilación del frontend.
- MySQL 8.4 con InnoDB. Acceso mediante MySQL Connector y SQL parametrizado; ningún ORM.
- CI como texto para preservar identidad y posibles ceros iniciales. No se inventa una persona diferente cuando se repite su CI.
- Claves primarias compuestas de cancha y equipo_jugador_torneo conservadas. En planilla se agrega UNIQUE(id_partido,ci_jugador) para evitar que la misma persona aparezca por ambos equipos y poder referenciarla desde goles y tarjetas.
- Se agrega UNIQUE(ci_jugador,id_torneo) para asegurar un solo equipo por edición.
- Las referencias compuestas del partido aseguran que los equipos pertenecen a su edición.
- El capitán permite NULL durante la construcción del equipo para resolver la dependencia circular jugador/plantel/equipo. La validación final de pertenencia al plantel y obligatoriedad está pendiente.
- Los identificadores SQL usan ASCII (`contrasena`, `direccion`); algunos valores de dominio también usan ASCII: `inscripcion` y `acumulacion de amarillas`.
- Resultado y posiciones derivados, sin un marcador editable redundante. Un autogol suma para el rival y no entra en el ranking de goleadores.
- Se devuelven los seis equipos en posiciones y fair play aunque no tengan eventos. Un 0–0 jugado cuenta como empate.
- Los reportes de partidos/goles/tarjetas cuentan partidos jugados. Uso de canchas mide partidos efectivamente jugados, no reservas. Participación ausente comprueba cualquier planilla registrada en la edición.
- El porcentaje por estado usa todos los partidos registrados como denominador, incluyendo programados; se muestran los estados presentes para no ocultar parte del total.
- Ranking de diez goleadores: empates ordenados por CI; máximo diez filas. Posiciones: puntos, diferencia y goles a favor; nombre solo da orden visual estable si persiste el empate, no una regla deportiva adicional.
- Nacimientos futuros, formatos básicos, dominios y referencias se validan en DB. El ABM valida también en Python y HTML; la DB sigue siendo la última defensa. Las validaciones de los módulos aún no implementados no se consideran cumplidas.

## Seguridad

Contraseñas de aplicación con PBKDF2-SHA256, sal aleatoria y 600.000 iteraciones. Sesiones firmadas, cookies HttpOnly/SameSite, formularios con token CSRF, escape automático de Jinja y parámetros en SQL. Se usan tres conexiones MySQL según la tarea: autenticación, administrador y planillero. No se confía únicamente en ocultar botones.

Las claves de demo son conocidas. Para desplegar: cambiar claves y hashes, activar HTTPS/cookies Secure, implementar limitación de intentos de login, gestión de usuarios y secretos externos. El avance solo está pensado para localhost.

Se restringe la escritura deportiva hasta completar procedimientos validados. Dar permisos directos de escritura sobre planillas/goles/tarjetas en esta etapa permitiría eludir reglas todavía pendientes.

## Mejoras propuestas

- Tablas auxiliares con índices únicos para ocupación de cancha/turno, equipo/fecha y pareja de rivales activa.
- Procedimientos o servicios transaccionales con bloqueos para todas las operaciones del torneo.
- Auditoría de altas, cambios, correcciones y sanciones; registro de usuario y hora.
- Campo de origen de sanción y restricciones de unicidad que permitan recalcular sanciones sin duplicarlas.
- Gestión de correcciones tardías y dependencia entre tarjetas, sanciones y planillas futuras.
- Guardar facultad/tipo históricos por inscripción si se permite modificarlos entre ediciones.

## Bitácora real de este avance

30/10/2026: lectura de las cuatro páginas de la consigna; verificación visual del modelo; creación del esquema y claves; preparación de datos ficticios; implementación de consultas, vistas, login, roles y ABM jugadores; documentación y pruebas portables.

Limitaciones del entorno: Docker Desktop no tenía el motor Linux iniciado; la descarga de dependencias falló por resolución de red. Por eso no se registran pruebas MySQL ni HTTP como realizadas. Consultar VALIDACION.md para el resultado comprobado. No se inventan horas de trabajo ni actividades de los estudiantes.

## Bibliografía y referencias para continuar

- UCU. Obligatorio BD — Segundo Semestre 2026. Consigna proporcionada por el estudiante, páginas 1–4.
- Python, documentación de biblioteca estándar: https://docs.python.org/3/
- Flask, documentación oficial: https://flask.palletsprojects.com/
- MySQL 8.4, manual de referencia: https://dev.mysql.com/doc/refman/8.4/en/
- MySQL Connector/Python: https://dev.mysql.com/doc/connector-python/en/
- Docker Compose: https://docs.docker.com/compose/

Los enlaces oficiales se incluyen como referencias de implementación; no sustituyen el registro de pruebas ni una revisión de todas sus páginas. Completar con fuentes efectivamente consultadas por el equipo y explicar en la defensa el código utilizado y la asistencia recibida.
