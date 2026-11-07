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

Segundo avance:
ABM de equipos

Se implementaron las operaciones para administrar los equipos participantes del torneo, permitiendo registrar nuevos equipos, consultar los existentes, modificar sus datos y eliminarlos.

Se incorporaron validaciones para controlar los datos ingresados y respetar las restricciones definidas en el modelo de datos.

ABM de planteles

Se implementó la gestión de los integrantes de cada equipo, incluyendo:

Incorporación de jugadores al plantel.

Eliminación de jugadores.

Asignación y modificación del capitán.

Consulta de los integrantes del equipo.

Se incorporaron las validaciones correspondientes a las reglas del torneo:

Los integrantes deben pertenecer a la misma facultad.

Un jugador no puede integrar más de un equipo en una misma edición.

El plantel puede tener como máximo diez integrantes.

Se permite un máximo de dos docentes o funcionarios.

El capitán debe formar parte del plantel.

Las modificaciones se permiten únicamente durante el período de inscripción.

Para las operaciones que involucran varios cambios relacionados se implementaron transacciones y bloqueos de registros, buscando mantener la consistencia de los datos ante errores o accesos concurrentes.

Se decidió permitir la construcción progresiva de los planteles, sin exigir el mínimo de cinco integrantes en cada incorporación. Este requisito debe controlarse al momento de habilitar la participación del equipo en el torneo.

ABM de complejos deportivos

Se implementaron las operaciones para registrar, consultar, modificar y eliminar complejos deportivos.

Se agregaron validaciones para controlar los campos obligatorios, las longitudes máximas y los datos ingresados.

También se contempló la relación entre complejos y canchas, manejando los errores de integridad referencial cuando se intenta eliminar un complejo que todavía tiene canchas asociadas.

ABM de canchas

Se implementaron las operaciones para registrar, consultar, modificar y eliminar canchas dentro de un complejo deportivo.

Se tuvieron en cuenta las restricciones del modelo de datos, particularmente la clave primaria compuesta por el nombre de la cancha y el identificador del complejo.

Se incorporaron validaciones para los campos de nombre, superficie y condición de cancha techada. Además, se contempló el manejo de errores por duplicación de claves para evitar que estas situaciones interrumpan la aplicación.

Gestión de planillas de partidos
Se implementó la gestión de planillas de partidos, permitiendo registrar los jugadores participantes de cada equipo y los eventos correspondientes al encuentro.

Se incorporaron las operaciones para:
  Registrar jugadores participantes.
  Registrar goles, indicando jugador y minuto.
  Registrar tarjetas amarillas y rojas, indicando jugador y minuto.
  Consultar los participantes y eventos registrados en cada partido.
Se incorporaron validaciones para asegurar que los jugadores registrados pertenezcan al plantel de alguno de los dos equipos participantes y que no estén suspendidos en la fecha correspondiente.

También se controla que solamente los jugadores incluidos en la planilla puedan convertir goles o recibir tarjetas.

El resultado del partido se calcula dinámicamente a partir de los goles registrados, contemplando también los autogoles. No se mantiene un resultado editable independiente de los eventos.

Se decidió que el registro de tarjetas forme parte de la gestión de planillas, sin implementar un ABM independiente para ellas.
ABM de sanciones
Se implementó la gestión de sanciones de jugadores, incluyendo:
  Alta de sanciones disciplinarias.
  Consulta de sanciones correspondientes al torneo seleccionado.
  Modificación de sanciones disciplinarias.
  Eliminación de sanciones disciplinarias.
Se incorporaron validaciones para comprobar que el jugador pertenezca a un plantel del torneo seleccionado y que la fecha de inicio y la cantidad de fechas de suspensión sean valores enteros positivos, con un máximo de 100.

Se decidió diferenciar las sanciones disciplinarias de las sanciones automáticas generadas por tarjetas:
  Las sanciones disciplinarias pueden registrarse, modificarse y eliminarse desde el ABM.
  Las sanciones por tarjeta roja y acumulación de amarillas se generan automáticamente mediante un trigger de MySQL.
  Las sanciones automáticas se muestran en la consulta, pero no pueden modificarse ni eliminarse desde el ABM.
Se incorporaron permisos de base de datos para permitir al administrador gestionar las sanciones disciplinarias.

**Gestión de ediciones y partidos**  
Se implementó la gestión de ediciones, la consulta del fixture y las operaciones administrativas para programar, modificar, reprogramar, cambiar el estado y eliminar partidos. Se agregaron validaciones de estados y reglas del torneo, junto con pruebas del dominio.  
Archivos relacionados: `torneos.py`, `partidos.py`, `domain.py`, `test_persona2.py`.

**Pantallas para fixture y ediciones**  
Se agregó la pantalla del fixture con selector de edición, listado de partidos y acciones administrativas, además de las pantallas de edición y gestión de torneos.  
Archivos relacionados: `fixture.html`, `edit_match.html`, `tournaments.html`.

**Permisos para operaciones administrativas**  
Se corrigieron los permisos de escritura del administrador para equipos, planteles, complejos y canchas. También se agregó el permiso necesario sobre turnos para las consultas con bloqueo usadas al gestionar partidos.  
Archivos relacionados: `04_permisos.sql`, `03_permisos_cancha.sql`, `04_permisos_admin_operaciones.sql`.

**Corrección del error al abrir el fixture**  
Se agregó la plantilla faltante que provocaba un error interno al entrar a la pestaña del fixture y se actualizó la descripción de las funcionalidades en el `README.md`.

**Aplicación y verificación de permisos en la base activa**  
Se aplicaron los permisos faltantes directamente a la base de datos que corre en Docker. Se comprobó que el usuario administrador pueda ejecutar las consultas con bloqueo sobre las tablas involucradas.

**Pruebas realizadas**  
Pasaron las 17 pruebas del proyecto. También se verificó que el fixture responda correctamente para las ediciones disponibles y que las consultas con bloqueo funcionen con los permisos del administrador.


## Bibliografía y referencias para continuar

- UCU. Obligatorio BD — Segundo Semestre 2026. Consigna proporcionada por el estudiante, páginas 1–4.
- Python, documentación de biblioteca estándar: https://docs.python.org/3/
- Flask, documentación oficial: https://flask.palletsprojects.com/
- MySQL 8.4, manual de referencia: https://dev.mysql.com/doc/refman/8.4/en/
- MySQL Connector/Python: https://dev.mysql.com/doc/connector-python/en/
- Docker Compose: https://docs.docker.com/compose/

Los enlaces oficiales se incluyen como referencias de implementación; no sustituyen el registro de pruebas ni una revisión de todas sus páginas. Completar con fuentes efectivamente consultadas por el equipo y explicar en la defensa el código utilizado y la asistencia recibida.
