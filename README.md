# Torneo Interfacultades UCU — avance

## Qué incluye

- Backend Python con Flask y MySQL Connector, SQL parametrizado directo, sin ORM.
- MySQL 8.4, las 14 estructuras mínimas de la consigna, claves y restricciones básicas.
- Inicio de sesión con contraseñas hash PBKDF2 y roles administrador/planillero.
- ABM de jugadores para el administrador. Baja protegida cuando existe historial.
- Fixture de consulta y 12 reportes (los 9 solicitados más 3 adicionales).
- 6 equipos, 36 jugadores, 3 fechas disputadas, 9 partidos jugados, autogol, tarjetas y sanciones de ejemplo.
- Perfiles MySQL diferentes; el planillero no puede escribir jugadores ni acceder al módulo de administración.
- Docker Compose y documentación de instalación, decisiones, pendientes y pruebas.

## Hasta ahora:


- **Base de datos y restricciones:** `sql/01_esquema.sql`. Crea las 14 tablas, claves primarias y foráneas, restricciones `CHECK` y `UNIQUE`, y triggers básicos.

- **Login y cierre de sesión:** `app/web.py`, funciones `login()`, `logout()` y `check_password()`. El formulario está en `app/templates/login.html`.

- **Control de acceso por rol:** `app/web.py`, decorador `required()`. Verifica la sesión y restringe las operaciones de administrador.

- **ABM de jugadores:** `app/web.py`, funciones `players()`, `edit_player()` y `delete_player()`. La pantalla está en `app/templates/players.html`. Permite crear, editar y eliminar jugadores; las referencias existentes impiden borrar jugadores con historial.

- **Validaciones de jugadores:** `app/domain.py`, función `validate_player()`. Comprueba CI, nombre, apellido, correo, nacimiento, facultad y tipo. Se complementa con validaciones HTML en `players.html` y restricciones SQL en `sql/01_esquema.sql`.

- **Consulta de equipos y planteles:** `app/web.py`, función `teams()`, y `app/templates/teams.html`. Muestra equipos por edición, facultad, capitán y jugadores. El acceso está en `app/templates/index.html`. Es una consulta para el administrador; todavía no permite modificar equipos ni planteles.

- **Equipos por edición en la lista de jugadores:** consulta `memberships` dentro de `players()` en `app/web.py`. La columna se muestra en `app/templates/players.html` y obtiene las inscripciones de `equipo_jugador_torneo`.

- **Consulta y gestión del fixture:** `app/partidos.py`, función `fixture_view()`, y `app/templates/fixture.html`. Muestra los partidos y resultados por edición; permite al administrador programar, modificar, reprogramar y cambiar el estado de partidos.

- **Cálculo de resultados y posiciones:** `sql/02_vistas.sql`. La vista `v_resultados` calcula los marcadores incluyendo autogoles; `v_actuaciones` obtiene la actuación de cada equipo por partido; y `v_posiciones` calcula estadísticas y puntos. El orden por puntos, diferencia de goles y goles a favor se aplica en el reporte de posiciones.

- **Reportes:** `app/reports.json`. Contiene los títulos y consultas de los nueve reportes solicitados y tres adicionales. La función `report()` de `app/web.py` ejecuta las consultas y `app/templates/table.html` presenta los resultados.

- **Datos de prueba:** `sql/03_datos.sql`. Incluye 6 equipos, 36 jugadores y 3 fechas disputadas, con goles, tarjetas y sanciones de ejemplo. Las sanciones de muestra se cargan explícitamente: todavía no se generan automáticamente.

- **Corrección de nombres de ejemplo:** `migrations/01_nombres_demo.sql`. Actualiza nombres y apellidos originales en una base existente sin cambiar CI ni relaciones. Las instrucciones están en `docs/ACTUALIZAR_NOMBRES.md`. Modificar el script de datos iniciales no actualiza una base ya creada.

- **Conexión y consultas parametrizadas:** `app/web.py`, función `query()`. Selecciona las credenciales según el rol y ejecuta SQL con parámetros mediante MySQL Connector.

- **Permisos en MySQL:** `sql/04_permisos.sql`. Crea usuarios separados para autenticación, administración y planillero. En este avance, el administrador puede gestionar jugadores y el planillero consultar el fixture; los permisos de escritura de los módulos futuros siguen pendientes.

- **Protección de formularios y sesiones:** `app/web.py`, funciones `csrf()` y `headers()`, y configuración de `app.config`. Los formularios incorporan tokens CSRF y las contraseñas se verifican mediante hash PBKDF2.

- **Diseño de la web:** `app/static/style.css`. Contiene los estilos con formato legible. En `app/templates/`, `base.html` define la estructura compartida, `index.html` la página de inicio y `error.html` los mensajes de error.

- **Ejecución con Docker:** `Dockerfile` y `compose.yaml`. Configuran los servicios de aplicación y MySQL.

- **Ejecución local con Python:** `run_local.py`. Lee `.env` desde la carpeta del script e inicia la aplicación. Las dependencias están en `requirements.txt` y la configuración de ejemplo en `.env.example`.

- **Pruebas básicas:** `tests/test_avance.py`. Incluye nueve pruebas de validaciones, coherencia de datos y cálculos. Se ejecutan desde la raíz del proyecto con `python -m unittest discover -s tests -v`.

- **Documentación:** carpeta `docs/`. Los archivos `INFORME.md`, `MODELO.md`, `REQUISITOS.md`, `VALIDACION.md` y `REVISION_AVANCE.md` incluyen decisiones, modelo, alcance, pruebas y revisión. Algunos registros históricos deben actualizarse al completar nuevas funcionalidades.

## Pendiente para completar el proyecto

- ABM de equipos y planteles, con validaciones de integrantes, facultad, capitán y etapa de inscripción.
- ABM de complejos deportivos y canchas.
- Gestión de las ediciones y sus estados.
- Registro de planillas, goles y tarjetas desde la web.
- Cierre de partidos y control del plazo de corrección de 48 horas.
- ABM de sanciones disciplinarias y generación automática de suspensiones.
- Permisos, transacciones y validaciones para los nuevos módulos.
- Pruebas integrales contra MySQL.
- Actualización final del informe y las instrucciones de instalación.


## Arranque : Docker Desktop

1. Extraer el ZIP y abrir una terminal dentro de la carpeta `Obligatorio_futbol_5_db`.
2. Iniciar Docker Desktop 
3. Copiar `.env.example` como `.env`:

```powershell
Copy-Item .env.example .env
docker compose up --build -d
docker compose ps
docker compose logs app
```

4. Abrir http://localhost:8000. El primer arranque necesita Internet para imágenes y dependencias.

| Rol | Correo | Contraseña local de demostración |
|---|---|---|
| Administrador | admin@demo.ucu | AdminDemo2026! |
| Planillero | planilla@demo.ucu | PlanillaDemo2026! |

Estas cuentas y las claves DB son públicas de ejemplo

### Recorrido de demostración

1. Ingresar como administrador.
2. Abrir la edición de demostración 2025 y consultar posiciones, goleadores, fair play y los demás reportes.
3. Abrir Jugadores y crear uno con una CI nueva; editarlo y eliminarlo antes de inscribirlo.
4. Intentar eliminar un jugador de los datos iniciales: sus referencias impiden borrar el historial.
5. Cerrar sesión e ingresar como planillero: se puede consultar el fixture; la carga de planillas aún no está implementada.

Los partidos de muestra son de 2025 para que ya hayan transcurrido sus turnos. La edición 2026 queda vacía, en inscripción, para continuar el desarrollo. Las fechas 4 y 5 del ejemplo tienen estados diversos para probar reportes; son un historial ficticio, no una agenda actual.

### Persistencia y reinicios

Los scripts `sql/01` a `sql/04` se ejecutan automáticamente solo al inicializar un volumen vacío. `docker compose down` detiene los servicios y conserva el volumen. `docker compose up -d` los vuelve a iniciar.
Editar un SQL no modifica una base ya inicializada: usar migraciones explícitas. No borrar el volumen si contiene trabajo que se quiera conservar

Si una base existente tiene permisos incompletos para las operaciones administrativas, aplicar `migrations/03_permisos_cancha.sql` y `migrations/04_permisos_admin_operaciones.sql` con una cuenta administradora de MySQL. La segunda migración habilita la gestión de equipos y planteles, complejos y canchas, además del permiso de actualización necesario para las lecturas con bloqueo de turnos al administrar partidos.

## Alternativa: Python y MySQL locales

Requiere Python 3.12 y MySQL 8.4. Crear una instancia/base de pruebas vacía y ejecutar, en el cliente mysql como administrador, en este orden:

```sql
SOURCE /ruta/absoluta/Obligatorio_futbol_5_db/sql/01_esquema.sql;
SOURCE /ruta/absoluta/Obligatorio_futbol_5_db/sql/02_vistas.sql;
SOURCE /ruta/absoluta/Obligatorio_futbol_5_db/sql/03_datos.sql;
SOURCE /ruta/absoluta/Obligatorio_futbol_5_db/sql/04_permisos.sql;
```

Los scripts crean `torneo_ucu`; no eliminan una base existente y no deben repetirse sobre tablas ya creadas.

```powershell
python -m venv .venv
.venv\Scripts\python Copy-Item .env.example .env
```

Agregar a `.env` `DB_HOST=127.0.0.1` y `DB_PORT=3306` (o el puerto real). Si MySQL corre con el Compose, usar 3307.

```powershell
.venv\Scripts\python run_local.py
```

En Linux/macOS usar `python3`, `cp` y `.venv/bin/python`. `run_local.py` usa el servidor de desarrollo para demostración local, sin debug. Docker usa Gunicorn.

## Pruebas incluidas

```powershell
python -m unittest discover -s tests -v
python -m compileall -q app run_local.py tests
docker compose config --quiet
```



Ver `docs/VALIDACION.md` para resultados reales y pruebas de integración pendientes. No se declara un arranque completo verificado hasta ejecutar el recorrido contra MySQL.

## Estructura

```text
app/                 Rutas, validación, consultas, plantillas y estilos
migrations/          Nombres demo
sql/                 Esquema, vistas, datos y permisos
tests/               Pruebas portables
docs/                Matriz de requisitos, informe y validación
compose.yaml         Servicios MySQL y aplicación
Dockerfile           Imagen de la aplicación
run_local.py         Inicio local con .env
```

Lo siguiente es implementar transacciones y procedimientos para planteles y programación de partidos; después planillas y sanciones automáticas. No conceder INSERT/UPDATE directos al planillero sobre tablas deportivas: usar operaciones controladas cuando sus validaciones estén implementadas.

## Revisión del avance

Ver docs/REVISION_AVANCE.md para el contraste con la consigna y los materiales.
