
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
    validate_correction_window,
    is_within_correction_window,
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
        "p.dia, t.hora_inicio, t.hora_fin, p.nombre_cancha, "
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
        "p.dia, t.hora_inicio, t.hora_fin, p.nombre_cancha, "
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

    editable = partido["estado"] != "cancelado" and is_within_correction_window(partido["dia"], partido["hora_fin"])
    if request.method == "POST":
        try:
            def guardar(cur):
                cur.callproc("validar_planilla", (id_partido,))
                cur.execute("SELECT p.*, t.hora_fin FROM partido p JOIN turno t USING(id_turno) WHERE id_partido=%s", (id_partido,))
                actual = cur.fetchone()
                if actual["estado"] == "cancelado":
                    raise ValueError("No se puede cargar una planilla de un partido cancelado.")
                validate_correction_window(actual["dia"], actual["hora_fin"])
                accion = request.form.get("accion", "")
                if accion == "agregar_participante":
                    ci = validate_ci(request.form.get("ci_jugador", ""))
                    cur.execute("INSERT INTO planilla_partido (id_partido,ci_jugador,id_equipo) SELECT %s,ci_jugador,id_equipo FROM equipo_jugador_torneo WHERE id_torneo=%s AND ci_jugador=%s AND id_equipo IN (%s,%s)", (id_partido,actual["id_torneo"],ci,actual["id_equipo_local"],actual["id_equipo_visitante"]))
                    if cur.rowcount != 1:
                        raise ValueError("El jugador no pertenece a los equipos del partido.")
                elif accion == "quitar_participante":
                    ci = validate_ci(request.form.get("ci_jugador", ""))
                    cur.execute("DELETE FROM planilla_partido WHERE id_partido=%s AND ci_jugador=%s", (id_partido,ci))
                elif accion in ("agregar_gol", "editar_gol", "eliminar_gol", "agregar_tarjeta", "editar_tarjeta", "eliminar_tarjeta"):
                    tabla = "gol" if accion.endswith("gol") else "tarjeta"
                    columna = "autogol" if tabla == "gol" else "color"
                    identificador = request.form.get("id_evento", "")
                    if not accion.startswith("agregar") and (not identificador.isdigit() or int(identificador) < 1):
                        raise ValueError("Evento inválido.")
                    if accion.startswith("eliminar"):
                        cur.execute(f"DELETE FROM {tabla} WHERE id_{tabla}=%s AND id_partido=%s", (identificador,id_partido))
                    else:
                        ci = validate_ci(request.form.get("ci_jugador", ""))
                        minuto = validate_minute(request.form.get("minuto", ""))
                        valor = request.form.get("autogol") == "1" if tabla == "gol" else validate_card_color(request.form.get("color", ""))
                        if accion.startswith("agregar"):
                            cur.execute(f"INSERT INTO {tabla} (id_partido,ci_jugador,minuto,{columna}) VALUES (%s,%s,%s,%s)", (id_partido,ci,minuto,valor))
                        else:
                            cur.execute(f"UPDATE {tabla} SET ci_jugador=%s,minuto=%s,{columna}=%s WHERE id_{tabla}=%s AND id_partido=%s", (ci,minuto,valor,identificador,id_partido))
                else:
                    raise ValueError("Acción inválida.")
            transaction(guardar)
            flash("Planilla actualizada.", "ok")
        except ValueError as error:
            flash(str(error), "error")
        except mysql.connector.Error as error:
            flash(getattr(error, "msg", "No se pudo actualizar la planilla."), "error")
        return redirect(url_for("planillas.detalle", id_partido=id_partido, torneo=partido["id_torneo"]))

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
        editable=editable,
        participantes=participantes,
        disponibles=disponibles,
        goles=goles,
        tarjetas=tarjetas,
        resultado=resultado,
    )
