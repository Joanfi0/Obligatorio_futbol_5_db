import os, json, secrets, hmac, hashlib
from pathlib import Path
from functools import wraps
from datetime import timedelta, date
import mysql.connector
from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash,
    abort,
)
from .domain import validate_player, TIPOS

app = Flask(__name__)
app.config.update(
    SECRET_KEY=os.environ["SECRET_KEY"],
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    PERMANENT_SESSION_LIFETIME=timedelta(minutes=30),
    MAX_CONTENT_LENGTH=32768,
)
REPORTS = json.loads(
    Path(__file__).with_name("reports.json").read_text(encoding="utf-8")
)


def query(sql, params=(), role=None, write=False):
    role = role or session.get("rol")
    cred = {
        "auth": ("torneo_auth", "DB_AUTH_PASSWORD"),
        "administrador": ("torneo_admin", "DB_ADMIN_PASSWORD"),
        "planillero": ("torneo_plan", "DB_PLAN_PASSWORD"),
    }
    if role not in cred:
        abort(403)
    user, key = cred[role]
    cn = mysql.connector.connect(
        host=os.getenv("DB_HOST", "127.0.0.1"),
        port=int(os.getenv("DB_PORT", "3307")),
        database=os.getenv("DB_NAME", "torneo_ucu"),
        user=user,
        password=os.environ[key],
        connection_timeout=5,
    )
    try:
        cur = cn.cursor(dictionary=True)
        cur.execute(sql, params)
        if write:
            cn.commit()
            return cur.rowcount
        return cur.fetchall()
    except Exception:
        if write:
            cn.rollback()
        raise
    finally:
        cn.close()


def required(admin=False):
    def deco(fn):
        @wraps(fn)
        def wrapped(*a, **kw):
            if "correo" not in session:
                return redirect(url_for("login"))
            if admin and session.get("rol") != "administrador":
                abort(403)
            return fn(*a, **kw)

        return wrapped

    return deco


@app.before_request
def csrf():
    if "csrf" not in session:
        session["csrf"] = secrets.token_hex(32)
    if request.method == "POST" and not hmac.compare_digest(
        session["csrf"], request.form.get("csrf", "")
    ):
        abort(400)


@app.after_request
def headers(response):
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Cache-Control"] = "no-store"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; style-src 'self'; form-action 'self'; frame-ancestors 'none'"
    )
    return response


def check_password(stored, pw):
    try:
        method, salt, want = stored.split("$")
        iterations = int(method.split(":")[2])
        got = hashlib.pbkdf2_hmac(
            "sha256", pw.encode(), salt.encode(), iterations
        ).hex()
        return hmac.compare_digest(got, want)
    except (ValueError, IndexError):
        return False


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        rows = query(
            "SELECT correo,contrasena,rol FROM login WHERE correo=%s",
            (request.form.get("correo", "").strip(),),
            role="auth",
        )
        if rows and check_password(
            rows[0]["contrasena"], request.form.get("password", "")
        ):
            session.clear()
            session.update(
                correo=rows[0]["correo"], rol=rows[0]["rol"], csrf=secrets.token_hex(32)
            )
            session.permanent = True
            return redirect(url_for("index"))
        flash("Correo o contrasena incorrectos.", "error")
    return render_template("login.html", title="Ingresar")


@app.post("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.get("/")
@required()
def index():
    tournaments = query("SELECT * FROM torneo ORDER BY anio DESC,semestre DESC")
    return render_template(
        "index.html",
        title="Torneo Interfacultades",
        tournaments=tournaments,
        reports=REPORTS,
    )


def torneo_id():
    try:
        n = int(request.args.get("torneo", "1"))
        if n < 1:
            raise ValueError()
        return n
    except ValueError:
        abort(400)


@app.get("/fixture")
@required()
def fixture():
    rows = query(
        "SELECT p.id_partido,p.numero_fecha,l.nombre local,v.nombre visitante,p.dia,t.hora_inicio,p.nombre_cancha,p.id_complejo,p.estado FROM partido p JOIN equipo l ON l.id_equipo=p.id_equipo_local JOIN equipo v ON v.id_equipo=p.id_equipo_visitante JOIN turno t ON t.id_turno=p.id_turno WHERE p.id_torneo=%s ORDER BY p.numero_fecha,p.dia,t.hora_inicio",
        (torneo_id(),),
    )
    return render_template("table.html", title="Fixture", rows=rows)


@app.get("/reportes/<key>")
@required(admin=True)
def report(key):
    if key not in REPORTS:
        abort(404)
    title, sql = REPORTS[key]
    rows = query(sql, (torneo_id(),))
    return render_template("table.html", title=title, rows=rows)


@app.route("/jugadores", methods=["GET", "POST"])
@required(admin=True)
def players():
    memberships = query("""
        SELECT ej.ci_jugador, e.nombre equipo, t.nombre torneo, t.anio, t.semestre
        FROM equipo_jugador_torneo ej
        JOIN equipo e ON e.id_equipo=ej.id_equipo AND e.id_torneo=ej.id_torneo
        JOIN torneo t ON t.id_torneo=ej.id_torneo
        ORDER BY t.anio DESC, t.semestre DESC, e.nombre
    """)
    if request.method == "POST":
        try:
            vals = validate_player(request.form)
            query(
                "INSERT INTO jugador (ci,nombre,apellido,email,fecha_nacimiento,id_facultad,tipo) VALUES (%s,%s,%s,%s,%s,%s,%s)",
                vals,
                write=True,
            )
            flash("Jugador creado. Aun no integra un plantel.", "ok")
            return redirect(url_for("players"))
        except ValueError as e:
            flash(str(e), "error")
        except mysql.connector.Error:
            flash(
                "No se pudo guardar. Verifica CI y correo unicos, facultad y fecha.",
                "error",
            )
    return render_template(
        "players.html",
        title="Jugadores",
        memberships=memberships,
        rows=query("SELECT * FROM jugador ORDER BY apellido,nombre"),
        faculties=query("SELECT * FROM facultad"),
        types=TIPOS,
        player=request.form if request.method == "POST" else {},
        editing=False,
        today=date.today().isoformat(),
    )


@app.route("/jugadores/<ci>/editar", methods=["GET", "POST"])
@required(admin=True)
def edit_player(ci):
    rows = query("SELECT * FROM jugador WHERE ci=%s", (ci,))
    if not rows:
        abort(404)
    if request.method == "POST":
        try:
            data = request.form.to_dict()
            data["ci"] = ci
            vals = validate_player(data)
            query(
                "UPDATE jugador SET nombre=%s,apellido=%s,email=%s,fecha_nacimiento=%s,id_facultad=%s,tipo=%s WHERE ci=%s",
                vals[1:] + (ci,),
                write=True,
            )
            flash("Jugador actualizado.", "ok")
            return redirect(url_for("players"))
        except ValueError as e:
            flash(str(e), "error")
        except mysql.connector.Error:
            flash(
                "No se pudo actualizar. Un jugador inscripto conserva facultad y tipo; el correo debe ser unico.",
                "error",
            )
    return render_template(
        "players.html",
        title="Editar jugador",
        rows=[],
        faculties=query("SELECT * FROM facultad"),
        types=TIPOS,
        player=request.form if request.method == "POST" else rows[0],
        editing=True,
        today=date.today().isoformat(),
    )


@app.post("/jugadores/<ci>/eliminar")
@required(admin=True)
def delete_player(ci):
    try:
        query("DELETE FROM jugador WHERE ci=%s", (ci,), write=True)
        flash("Baja procesada.", "ok")
    except mysql.connector.Error:
        flash(
            "No se puede eliminar: existen referencias (plantel, capitania o historial).",
            "error",
        )
    return redirect(url_for("players"))


@app.errorhandler(mysql.connector.Error)
def database_error(error):
    app.logger.error(
        "Error de conexion o consulta MySQL: %s", getattr(error, "errno", None)
    )
    return (
        render_template(
            "error.html",
            title="Base de datos no disponible",
            message="Verifica que MySQL este iniciado y las credenciales coincidan con la instalacion.",
        ),
        503,
    )


@app.errorhandler(403)
def forbidden(error):
    return (
        render_template(
            "error.html",
            title="Acceso restringido",
            message="Tu rol no tiene permiso para esta operacion.",
        ),
        403,
    )


@app.get("/equipos")
@required(admin=True)
def teams():
    edition = torneo_id()
    tournaments = query("SELECT * FROM torneo WHERE id_torneo=%s", (edition,))
    if not tournaments:
        abort(404)
    rows = query(
        """
        SELECT e.id_equipo, e.nombre, f.nombre facultad,
               j.nombre capitan_nombre, j.apellido capitan_apellido
        FROM equipo e
        JOIN facultad f ON f.id_facultad=e.id_facultad
        LEFT JOIN jugador j ON j.ci=e.ci_capitan
        WHERE e.id_torneo=%s
        ORDER BY e.nombre
    """,
        (edition,),
    )
    rosters = query(
        """
        SELECT ej.id_equipo, ej.numero_camiseta, j.ci, j.nombre,
               j.apellido, j.tipo, (e.ci_capitan=j.ci) capitan
        FROM equipo_jugador_torneo ej
        JOIN jugador j ON j.ci=ej.ci_jugador
        JOIN equipo e ON e.id_equipo=ej.id_equipo AND e.id_torneo=ej.id_torneo
        WHERE ej.id_torneo=%s
        ORDER BY ej.numero_camiseta, j.apellido
    """,
        (edition,),
    )
    return render_template(
        "teams.html",
        title="Equipos",
        teams=rows,
        rosters=rosters,
        tournament=tournaments[0],
    )
