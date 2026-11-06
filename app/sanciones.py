import mysql.connector

from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
)

from .domain import (
    validate_ci,
    validate_matchday,
    validate_suspension,
)
from .web import query, required


sanciones_bp = Blueprint("sanciones", __name__)


@sanciones_bp.route("/", methods=["GET", "POST"])
@required(admin=True)
def index():
    torneos = query(
        "SELECT id_torneo, nombre, anio, semestre "
        "FROM torneo "
        "ORDER BY anio DESC, semestre DESC"
    )

    if not torneos:
        return render_template(
            "sanctions.html",
            torneos=[],
            torneo=None,
            jugadores=[],
            sanciones=[],
        )

    torneo_seleccionado = request.args.get("torneo", "").strip()

    if request.method == "POST":
        torneo_seleccionado = request.form.get(
            "id_torneo", ""
        ).strip()

        try:
            if not torneo_seleccionado.isdigit():
                raise ValueError("Debes seleccionar un torneo.")

            id_torneo = int(torneo_seleccionado)

            if not any(
                t["id_torneo"] == id_torneo for t in torneos
            ):
                raise ValueError("El torneo seleccionado no es válido.")

            accion = request.form.get("accion", "").strip()

            if accion == "registrar":
                ci_jugador = validate_ci(
                    request.form.get("ci_jugador", "")
                )
                numero_fecha_inicio = validate_matchday(
                    request.form.get("numero_fecha_inicio", "")
                )
                cantidad_fechas = validate_suspension(
                    request.form.get("cantidad_fechas", "")
                )

                jugador = query(
                    "SELECT ci_jugador "
                    "FROM equipo_jugador_torneo "
                    "WHERE ci_jugador = %s AND id_torneo = %s",
                    (ci_jugador, id_torneo),
                )

                if not jugador:
                    raise ValueError(
                        "El jugador no pertenece a ningún plantel de ese torneo."
                    )

                query(
                    "INSERT INTO sancion_jugador "
                    "(ci_jugador, id_torneo, motivo, "
                    "numero_fecha_inicio, cantidad_fechas) "
                    "VALUES (%s, %s, 'disciplinaria', %s, %s)",
                    (
                        ci_jugador,
                        id_torneo,
                        numero_fecha_inicio,
                        cantidad_fechas,
                    ),
                    write=True,
                )

                flash("Sanción registrada correctamente.", "success")

            elif accion == "modificar":
                id_sancion = request.form.get(
                    "id_sancion", ""
                ).strip()

                if not id_sancion.isdigit() or int(id_sancion) <= 0:
                    raise ValueError("La sanción seleccionada no es válida.")

                id_sancion = int(id_sancion)

                numero_fecha_inicio = validate_matchday(
                    request.form.get("numero_fecha_inicio", "")
                )
                cantidad_fechas = validate_suspension(
                    request.form.get("cantidad_fechas", "")
                )

                resultado = query(
                    "UPDATE sancion_jugador "
                    "SET numero_fecha_inicio = %s, "
                    "cantidad_fechas = %s "
                    "WHERE id_sancion = %s "
                    "AND id_torneo = %s "
                    "AND motivo = 'disciplinaria'",
                    (
                        numero_fecha_inicio,
                        cantidad_fechas,
                        id_sancion,
                        id_torneo,
                    ),
                    write=True,
                )

                if resultado:
                    flash("Sanción modificada correctamente.", "success")
                else:
                    flash(
                        "No se encontró la sanción o no es una sanción disciplinaria.",
                        "error",
                    )

            elif accion == "eliminar":
                id_sancion = request.form.get(
                    "id_sancion", ""
                ).strip()

                if not id_sancion.isdigit() or int(id_sancion) <= 0:
                    raise ValueError("La sanción seleccionada no es válida.")

                id_sancion = int(id_sancion)

                resultado = query(
                    "DELETE FROM sancion_jugador "
                    "WHERE id_sancion = %s "
                    "AND id_torneo = %s "
                    "AND motivo = 'disciplinaria'",
                    (id_sancion, id_torneo),
                    write=True,
                )

                if resultado:
                    flash("Sanción eliminada correctamente.", "success")
                else:
                    flash(
                        "No se encontró la sanción o no es una sanción disciplinaria.",
                        "error",
                    )

            else:
                raise ValueError("La operación solicitada no es válida.")

        except ValueError as error:
            flash(str(error), "error")

        except mysql.connector.IntegrityError:
            flash(
                "No se pudo realizar la operación por una restricción de la base de datos.",
                "error",
            )

        return redirect(
            url_for("sanciones.index", torneo=torneo_seleccionado)
        )

    try:
        id_torneo = int(torneo_seleccionado)
    except (TypeError, ValueError):
        id_torneo = torneos[0]["id_torneo"]

    if not any(t["id_torneo"] == id_torneo for t in torneos):
        id_torneo = torneos[0]["id_torneo"]

    torneo = next(
        t for t in torneos if t["id_torneo"] == id_torneo
    )

    jugadores = query(
        "SELECT j.ci, j.nombre, j.apellido, e.nombre AS equipo "
        "FROM equipo_jugador_torneo ej "
        "JOIN jugador j ON j.ci = ej.ci_jugador "
        "JOIN equipo e ON e.id_equipo = ej.id_equipo "
        "WHERE ej.id_torneo = %s "
        "ORDER BY e.nombre, j.apellido, j.nombre",
        (id_torneo,),
    )

    sanciones = query(
        "SELECT s.id_sancion, s.ci_jugador, "
        "j.nombre, j.apellido, e.nombre AS equipo, "
        "s.motivo, s.numero_fecha_inicio, s.cantidad_fechas "
        "FROM sancion_jugador s "
        "JOIN jugador j ON j.ci = s.ci_jugador "
        "JOIN equipo_jugador_torneo ej "
        "ON ej.ci_jugador = s.ci_jugador "
        "AND ej.id_torneo = s.id_torneo "
        "JOIN equipo e ON e.id_equipo = ej.id_equipo "
        "WHERE s.id_torneo = %s "
        "ORDER BY s.numero_fecha_inicio, j.apellido, j.nombre",
        (id_torneo,),
    )

    return render_template(
        "sanctions.html",
        torneos=torneos,
        torneo=torneo,
        jugadores=jugadores,
        sanciones=sanciones,
    )