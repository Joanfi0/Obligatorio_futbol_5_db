# Torneo Interfacultades UCU — avance

Base de proyecto para continuar el obligatorio de Bases de Datos I, segundo semestre de 2026.
**Es un avance, no una entrega final completa.**  avance el 30/10, entrega final el 06/11 y defensa el 13/11.

## Qué incluye

- Backend Python con Flask y MySQL Connector, SQL parametrizado directo, sin ORM.
- MySQL 8.4, las 14 estructuras mínimas de la consigna, claves y restricciones básicas.
- Inicio de sesión con contraseñas hash PBKDF2 y roles administrador/planillero.
- ABM de jugadores para el administrador. Baja protegida cuando existe historial.
- Fixture de consulta y 12 reportes (los 9 solicitados más 3 adicionales).
- 6 equipos, 36 jugadores, 3 fechas disputadas, 9 partidos jugados, autogol, tarjetas y sanciones de ejemplo.
- Perfiles MySQL diferentes; el planillero no puede escribir jugadores ni acceder al módulo de administración.
- Docker Compose y documentación de instalación, decisiones, pendientes y pruebas.

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

Estas cuentas y las claves DB son públicas de ejemplo: NO usar en Internet. No subir `.env` a GitHub.
La aplicación se publica solo en la interfaz local. No usa la cuenta root de MySQL.

### Recorrido de demostración

1. Ingresar como administrador.
2. Abrir la edición de demostración 2025 y consultar posiciones, goleadores, fair play y los demás reportes.
3. Abrir Jugadores y crear uno con una CI nueva; editarlo y eliminarlo antes de inscribirlo.
4. Intentar eliminar un jugador de los datos iniciales: sus referencias impiden borrar el historial.
5. Cerrar sesión e ingresar como planillero: se puede consultar el fixture; la carga de planillas aún no está implementada.

Los partidos de muestra son de 2025 para que ya hayan transcurrido sus turnos. La edición 2026 queda vacía, en inscripción, para continuar el desarrollo. Las fechas 4 y 5 del ejemplo tienen estados diversos para probar reportes; son un historial ficticio, no una agenda actual.

### Persistencia y reinicios

Los scripts `sql/01` a `sql/04` se ejecutan automáticamente solo al inicializar un volumen vacío. `docker compose down` detiene los servicios y conserva el volumen. `docker compose up -d` los vuelve a iniciar.
Editar un SQL no modifica una base ya inicializada: usar migraciones explícitas. No borrar el volumen si contiene trabajo que quieras conservar.

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

Las pruebas portables usan solo la biblioteca estándar; comprueban validación, coherencia del fixture y lógica de reportes con un oráculo SQLite en memoria. **La aplicación y los scripts de instalación usan exclusivamente MySQL.** Este oráculo no valida el dialecto, los triggers, los grants ni la concurrencia de MySQL.

Ver `docs/VALIDACION.md` para resultados reales y pruebas de integración pendientes. No se declara un arranque completo verificado hasta ejecutar el recorrido contra MySQL.

## Estructura

```text
app/                 Rutas, validación, consultas, plantillas y estilos
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

## Corrección de datos y consulta de equipos

Se reemplazaron los 36 nombres de muestra por nombres y apellidos ficticios realistas. Se agregó consulta de equipos/planteles para administrador por edición y una columna de inscripciones en Jugadores. El ABM de equipos sigue pendiente. Para bases existentes ver docs/ACTUALIZAR_NOMBRES.md (ACTUALIZAR_NOMBRES.md desde esta carpeta). Pasaron las 9 pruebas y comprobaciones de rutas/consultas con SQLite; no se ejecutó integración MySQL.
