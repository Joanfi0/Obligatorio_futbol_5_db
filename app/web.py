
import os
import json
import secrets
import hmac
import hashlib
from pathlib import Path
from functools import wraps
from datetime import timedelta

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

def transaction(operation, role=None):
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

    cur = None

    try:
        cn.start_transaction()
        cur = cn.cursor(dictionary=True)

        result = operation(cur)

        cn.commit()
        return result

    except Exception:
        cn.rollback()
        raise

    finally:
        if cur:
            cur.close()
        cn.close()

@app.before_request
def csrf():
    if "csrf" not in session:
        session["csrf"] = secrets.token_hex(32)

    if request.method == "POST" and not hmac.compare_digest(
        session["csrf"],
        request.form.get("csrf", ""),
    ):
        abort(400)


@app.after_request
def headers(response):
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Cache-Control"] = "no-store"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; style-src 'self'; "
        "form-action 'self'; frame-ancestors 'none'"
    )
    return response


def check_password(stored, pw):
    try:
        method, salt, want = stored.split("$")
        iterations = int(method.split(":")[2])

        got = hashlib.pbkdf2_hmac(
            "sha256",
            pw.encode(),
            salt.encode(),
            iterations,
        ).hex()

        return hmac.compare_digest(got, want)

    except (ValueError, IndexError):
        return False

def hash_password(pw, iterations=600000):
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        pw.encode("utf-8"),
        salt.encode("utf-8"),
        iterations,
    ).hex()
    return f"pbkdf2:sha256:{iterations}${salt}${digest}"


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        rows = query(
            "SELECT correo,contrasena,rol FROM login WHERE correo=%s",
            (request.form.get("correo", "").strip(),),
            role="auth",
        )

        if rows and check_password(
            rows[0]["contrasena"],
            request.form.get("password", ""),
        ):
            session.clear()
            session.update(
                correo=rows[0]["correo"],
                rol=rows[0]["rol"],
                csrf=secrets.token_hex(32),
            )
            session.permanent = True
            return redirect(url_for("index"))

        flash("Correo o contraseña incorrectos.", "error")

    return render_template("login.html", title="Ingresar")


@app.post("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.get("/")
@required()
def index():
    tournaments = query(
        "SELECT * FROM torneo ORDER BY anio DESC,semestre DESC"
    )

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



@app.get("/reportes/<key>")
@required(admin=True)
def report(key):
    if key not in REPORTS:
        abort(404)

    title, sql = REPORTS[key]
    rows = query(sql, (torneo_id(),))

    return render_template("table.html", title=title, rows=rows)


@app.errorhandler(mysql.connector.Error)
def database_error(error):
    app.logger.exception("Error de conexión o consulta MySQL")

    return (
        render_template(
            "error.html",
            title="Base de datos no disponible",
            message="Verifica que MySQL esté iniciado y las credenciales coincidan con la instalación.",
        ),
        503,
    )


@app.errorhandler(403)
def forbidden(error):
    return (
        render_template(
            "error.html",
            title="Acceso restringido",
            message="Tu rol no tiene permiso para esta operación.",
        ),
        403,
    )


# Registro de Blueprints
from .jugadores import jugadores_bp
from .equipos import equipos_bp
from .planteles import planteles_bp
from .complejos import complejos_bp
from .canchas import canchas_bp
from .torneos import torneos_bp
from .partidos import partidos_bp, fixture_view

app.register_blueprint(canchas_bp)
app.register_blueprint(complejos_bp)
app.register_blueprint(planteles_bp)
app.register_blueprint(jugadores_bp)
app.register_blueprint(equipos_bp)
app.register_blueprint(torneos_bp)
app.register_blueprint(partidos_bp)


app.add_url_rule("/fixture", endpoint="fixture", view_func=fixture_view)