
import mysql.connector

from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    abort,
)

from .domain import (
    validate_ci,
    validate_minute,
    validate_card_color,
)
from .web import query, transaction, required, torneo_id


planillas_bp = Blueprint("planillas", __name__)


@planillas_bp.get("/")
@required(planillero=True)
def index():
    rows = query(
        "SELECT p.id_partido, p.numero_fecha, "
        "l.nombre AS local, v.nombre AS visitante, "
        "p.dia, t.hora_inicio, p.nombre_cancha, "
        "p.id_complejo, p.estado, "
        "(SELECT COUNT(*) "
        " FROM planilla_partido pp "
        " WHERE pp.id_partido = p.id_partido) AS participantes "
        "FROM partido p "
        "JOIN equipo l ON l.id_equipo = p.id_equipo_local "
        "JOIN equipo v ON v.id_equipo = p.id_equipo_visitante "
        "JOIN turno t ON t.id_turno = p.id_turno "
        "WHERE p.id_torneo = %s "
        "ORDER BY p.numero_fecha, p.dia, t.hora_inicio",
        (torneo_id(),),
    )

    return render_template(
        "score_sheets.html",
        rows=rows,
    )


@planillas_bp.route("/<int:id_partido>", methods=["GET", "POST"])
@required(planillero=True)
def detalle(id_partido):
    partido = query(
        "SELECT p.id_partido, p.numero_fecha, "
        "p.id_torneo, p.id_equipo_local, p.id_equipo_visitante, "
        "l.nombre AS local, v.nombre AS visitante, "
        "p.dia, t.hora_inicio, p.nombre_cancha, "
        "p.id_complejo, p.estado "
        "FROM partido p "
        "JOIN equipo l ON l.id_equipo = p.id_equipo_local "
        "JOIN equipo v ON v.id_equipo = p.id_equipo_visitante "
        "JOIN turno t ON t.id_turno = p.id_turno "
        "WHERE p.id_partido = %s AND p.id_torneo = %s",
        (id_partido, torneo_id()),
    )

    if not partido:
        abort(404)

    partido = partido[0]

    if request.method == "POST":
        accion = request.form.get("accion")
        ci_jugador = request.form.get("ci_jugador", "")

        try:
            if accion not in (
                "agregar_participante",
                "agregar_gol",
                "agregar_tarjeta",
            ):
                raise ValueError("La acción solicitada no es válida.")

            ci_jugador = validate_ci(ci_jugador)

            if accion == "agregar_participante":

                def agregar_participante(cur):
                    cur.execute(
                        "INSERT INTO planilla_partido "
                        "(id_partido, ci_jugador, id_equipo) "
                        "SELECT p.id_partido, ej.ci_jugador, ej.id_equipo "
                        "FROM partido p "
                        "JOIN equipo_jugador_torneo ej "
                        "ON ej.id_torneo = p.id_torneo "
                        "AND ej.id_equipo IN "
                        "(p.id_equipo_local, p.id_equipo_visitante) "
                        "WHERE p.id_partido = %s "
                        "AND ej.ci_jugador = %s "
                        "AND NOT EXISTS ("
                        "    SELECT 1 "
                        "    FROM sancion_jugador s "
                        "    WHERE s.ci_jugador = ej.ci_jugador "
                        "    AND s.id_torneo = p.id_torneo "
                        "    AND p.numero_fecha >= s.numero_fecha_inicio "
                        "    AND p.numero_fecha < "
                        "        s.numero_fecha_inicio + s.cantidad_fechas"
                        ")",
                        (id_partido, ci_jugador),
                    )

                    if cur.rowcount != 1:
                        raise ValueError(
                            "El jugador no pertenece a ninguno de los equipos "
                            "del partido o está suspendido."
                        )

                transaction(agregar_participante)

                flash("Participante agregado correctamente.", "success")

            elif accion == "agregar_gol":
                minuto = validate_minute(
                    request.form.get("minuto", "")
                )
                autogol = request.form.get("autogol") == "1"

                def agregar_gol(cur):
                    cur.execute(
                        "INSERT INTO gol "
                        "(id_partido, ci_jugador, minuto, autogol) "
                        "SELECT id_partido, ci_jugador, %s, %s "
                        "FROM planilla_partido "
                        "WHERE id_partido = %s AND ci_jugador = %s",
                        (minuto, autogol, id_partido, ci_jugador),
                    )

                    if cur.rowcount != 1:
                        raise ValueError(
                            "El jugador no está registrado en la planilla."
                        )

                transaction(agregar_gol)

                flash("Gol registrado correctamente.", "success")

            elif accion == "agregar_tarjeta":
                minuto = validate_minute(
                    request.form.get("minuto", "")
                )
                color = validate_card_color(
                    request.form.get("color", "")
                )

                def agregar_tarjeta(cur):
                    cur.execute(
                        "INSERT INTO tarjeta "
                        "(id_partido, ci_jugador, minuto, color) "
                        "SELECT id_partido, ci_jugador, %s, %s "
                        "FROM planilla_partido "
                        "WHERE id_partido = %s AND ci_jugador = %s",
                        (minuto, color, id_partido, ci_jugador),
                    )

                    if cur.rowcount != 1:
                        raise ValueError(
                            "El jugador no está registrado en la planilla."
                        )

                transaction(agregar_tarjeta)

                flash("Tarjeta registrada correctamente.", "success")

        except ValueError as error:
            flash(str(error), "error")

        except mysql.connector.IntegrityError:
            flash(
                "No se pudo registrar el dato por una restricción de la base de datos.",
                "error",
            )

        return redirect(
            url_for("planillas.detalle", id_partido=id_partido)
        )

    participantes = query(
        "SELECT pp.ci_jugador, j.nombre, j.apellido, "
        "e.nombre AS equipo, ej.numero_camiseta "
        "FROM planilla_partido pp "
        "JOIN jugador j ON j.ci = pp.ci_jugador "
        "JOIN equipo e ON e.id_equipo = pp.id_equipo "
        "JOIN equipo_jugador_torneo ej "
        "ON ej.id_equipo = pp.id_equipo "
        "AND ej.ci_jugador = pp.ci_jugador "
        "AND ej.id_torneo = %s "
        "WHERE pp.id_partido = %s "
        "ORDER BY e.nombre, ej.numero_camiseta",
        (partido["id_torneo"], id_partido),
    )

    disponibles = query(
        "SELECT j.ci AS ci_jugador, j.nombre, j.apellido, "
        "e.nombre AS equipo, ej.numero_camiseta "
        "FROM partido p "
        "JOIN equipo_jugador_torneo ej "
        "ON ej.id_torneo = p.id_torneo "
        "AND ej.id_equipo IN "
        "(p.id_equipo_local, p.id_equipo_visitante) "
        "JOIN jugador j ON j.ci = ej.ci_jugador "
        "JOIN equipo e ON e.id_equipo = ej.id_equipo "
        "WHERE p.id_partido = %s "
        "AND NOT EXISTS ("
        "    SELECT 1 "
        "    FROM planilla_partido pp "
        "    WHERE pp.id_partido = p.id_partido "
        "    AND pp.ci_jugador = j.ci"
        ") "
        "AND NOT EXISTS ("
        "    SELECT 1 "
        "    FROM sancion_jugador s "
        "    WHERE s.ci_jugador = j.ci "
        "    AND s.id_torneo = p.id_torneo "
        "    AND p.numero_fecha >= s.numero_fecha_inicio "
        "    AND p.numero_fecha < "
        "        s.numero_fecha_inicio + s.cantidad_fechas"
        ") "
        "ORDER BY e.nombre, ej.numero_camiseta",
        (id_partido,),
    )

    goles = query(
        "SELECT g.id_gol, g.ci_jugador, j.nombre, j.apellido, "
        "g.minuto, g.autogol "
        "FROM gol g "
        "JOIN jugador j ON j.ci = g.ci_jugador "
        "WHERE g.id_partido = %s "
        "ORDER BY g.minuto, g.id_gol",
        (id_partido,),
    )

    tarjetas = query(
        "SELECT t.id_tarjeta, t.ci_jugador, j.nombre, j.apellido, "
        "t.minuto, t.color "
        "FROM tarjeta t "
        "JOIN jugador j ON j.ci = t.ci_jugador "
        "WHERE t.id_partido = %s "
        "ORDER BY t.minuto, t.id_tarjeta",
        (id_partido,),
    )

    resultado = query(
        "SELECT "
        "COALESCE(SUM(CASE "
        "    WHEN (pp.id_equipo = p.id_equipo_local AND g.autogol = 0) "
        "      OR (pp.id_equipo = p.id_equipo_visitante AND g.autogol = 1) "
        "    THEN 1 ELSE 0 "
        "END), 0) AS goles_local, "
        "COALESCE(SUM(CASE "
        "    WHEN (pp.id_equipo = p.id_equipo_visitante AND g.autogol = 0) "
        "      OR (pp.id_equipo = p.id_equipo_local AND g.autogol = 1) "
        "    THEN 1 ELSE 0 "
        "END), 0) AS goles_visitante "
        "FROM partido p "
        "LEFT JOIN gol g ON g.id_partido = p.id_partido "
        "LEFT JOIN planilla_partido pp "
        "ON pp.id_partido = g.id_partido "
        "AND pp.ci_jugador = g.ci_jugador "
        "WHERE p.id_partido = %s",
        (id_partido,),
    )[0]

    return render_template(
        "score_sheet_detail.html",
        partido=partido,
        participantes=participantes,
        disponibles=disponibles,
        goles=goles,
        tarjetas=tarjetas,
        resultado=resultado,
    )
