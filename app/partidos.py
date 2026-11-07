import mysql.connector
from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from .web import query, transaction, required
from .domain import (
    ESTADOS_PARTIDO,
    SagaCoordinator,
    validate_match_form,
    validate_match_rules,
    can_mark_match_played,
    is_within_correction_window,
    validate_correction_window,
)

partidos_bp = Blueprint("partidos", __name__)


def _execute_match_write_saga(cur, match_data, editing_id=None):
    """
    Ejecuta la reserva y persistencia de un partido combinando bloqueo pesimista
    InnoDB (FOR UPDATE) con el coordinador Saga de pasos y compensaciones.
    """
    context = {}
    saga = SagaCoordinator()

    def step_lock_context():
        cur.execute(
            "SELECT * FROM torneo WHERE id_torneo=%s FOR UPDATE",
            (match_data["id_torneo"],),
        )
        context["tournament"] = cur.fetchone()

        cur.execute(
            "SELECT * FROM cancha WHERE id_complejo=%s AND nombre_cancha=%s FOR UPDATE",
            (match_data["id_complejo"], match_data["nombre_cancha"]),
        )
        if not cur.fetchone():
            raise ValueError("La cancha seleccionada no existe en ese complejo.")

        cur.execute(
            "SELECT * FROM turno WHERE id_turno=%s",
            (match_data["id_turno"],),
        )
        turno = cur.fetchone()
        if not turno:
            raise ValueError("El turno seleccionado no existe.")
        context["hora_fin"] = turno["hora_fin"]

        if editing_id is not None:
            cur.execute(
                "SELECT p.*, t.hora_fin FROM partido p "
                "JOIN turno t ON t.id_turno = p.id_turno "
                "WHERE p.id_partido=%s FOR UPDATE",
                (editing_id,),
            )
            old_match = cur.fetchone()
            if not old_match:
                raise ValueError("El partido que intenta editar no existe.")
            context["editing_match"] = old_match
        else:
            context["editing_match"] = None

    def step_verify_rosters_and_conflicts():
        cur.execute(
            "SELECT id_equipo, nombre, id_torneo, id_facultad "
            "FROM equipo WHERE id_torneo=%s FOR UPDATE",
            (match_data["id_torneo"],),
        )
        teams_by_id = {r["id_equipo"]: r for r in cur.fetchall()}

        cur.execute(
            "SELECT id_equipo, COUNT(*) AS total "
            "FROM equipo_jugador_torneo WHERE id_torneo=%s "
            "GROUP BY id_equipo",
            (match_data["id_torneo"],),
        )
        roster_counts = {r["id_equipo"]: r["total"] for r in cur.fetchall()}

        cur.execute(
            "SELECT * FROM partido "
            "WHERE id_torneo=%s OR (dia=%s AND id_turno=%s AND nombre_cancha=%s AND id_complejo=%s) "
            "FOR UPDATE",
            (
                match_data["id_torneo"],
                match_data["dia"],
                match_data["id_turno"],
                match_data["nombre_cancha"],
                match_data["id_complejo"],
            ),
        )
        existing_matches = cur.fetchall()

        validate_match_rules(
            match_data=match_data,
            tournament=context["tournament"],
            teams_by_id=teams_by_id,
            roster_counts=roster_counts,
            existing_matches=existing_matches,
            shift_end_time=context["hora_fin"],
            editing_match=context["editing_match"],
        )

    def step_persist_match():
        if editing_id is None:
            cur.execute(
                "INSERT INTO partido "
                "(id_torneo, numero_fecha, id_equipo_local, id_equipo_visitante, "
                "dia, id_turno, nombre_cancha, id_complejo, estado) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
                (
                    match_data["id_torneo"],
                    match_data["numero_fecha"],
                    match_data["id_equipo_local"],
                    match_data["id_equipo_visitante"],
                    match_data["dia"],
                    match_data["id_turno"],
                    match_data["nombre_cancha"],
                    match_data["id_complejo"],
                    match_data["estado"],
                ),
            )
            context["persisted_id"] = cur.lastrowid
        else:
            cur.execute(
                "UPDATE partido SET numero_fecha=%s, id_equipo_local=%s, "
                "id_equipo_visitante=%s, dia=%s, id_turno=%s, "
                "nombre_cancha=%s, id_complejo=%s, estado=%s "
                "WHERE id_partido=%s",
                (
                    match_data["numero_fecha"],
                    match_data["id_equipo_local"],
                    match_data["id_equipo_visitante"],
                    match_data["dia"],
                    match_data["id_turno"],
                    match_data["nombre_cancha"],
                    match_data["id_complejo"],
                    match_data["estado"],
                    editing_id,
                ),
            )
            context["persisted_id"] = editing_id

    def compensate_persist():
        if editing_id is None and context.get("persisted_id"):
            cur.execute(
                "DELETE FROM partido WHERE id_partido=%s",
                (context["persisted_id"],),
            )
        elif editing_id is not None and context.get("editing_match"):
            old = context["editing_match"]
            cur.execute(
                "UPDATE partido SET numero_fecha=%s, id_equipo_local=%s, "
                "id_equipo_visitante=%s, dia=%s, id_turno=%s, "
                "nombre_cancha=%s, id_complejo=%s, estado=%s "
                "WHERE id_partido=%s",
                (
                    old["numero_fecha"],
                    old["id_equipo_local"],
                    old["id_equipo_visitante"],
                    old["dia"],
                    old["id_turno"],
                    old["nombre_cancha"],
                    old["id_complejo"],
                    old["estado"],
                    editing_id,
                ),
            )

    saga.add_step("lock_context", step_lock_context)
    saga.add_step("verify_rules", step_verify_rosters_and_conflicts)
    saga.add_step("persist_match", step_persist_match, compensate_persist)
    saga.execute()
    return context.get("persisted_id")


@partidos_bp.get("/fixture")
@required()
def fixture_view():
    try:
        id_torneo = int(request.args.get("torneo", "1"))
        if id_torneo < 1:
            raise ValueError()
    except ValueError:
        abort(400)

    tournaments = query("SELECT * FROM torneo ORDER BY anio DESC, semestre DESC")
    current_torneo = next(
        (t for t in tournaments if t["id_torneo"] == id_torneo), None
    )
    if not current_torneo and tournaments:
        current_torneo = tournaments[0]
        id_torneo = current_torneo["id_torneo"]

    rows = query(
        "SELECT p.id_partido, p.id_torneo, p.numero_fecha, "
        "p.id_equipo_local, p.id_equipo_visitante, "
        "l.nombre AS local, v.nombre AS visitante, "
        "p.dia, p.id_turno, t.hora_inicio, t.hora_fin, "
        "p.nombre_cancha, p.id_complejo, c.nombre AS complejo, p.estado, "
        "r.goles_local, r.goles_visitante "
        "FROM partido p "
        "JOIN equipo l ON l.id_equipo = p.id_equipo_local "
        "JOIN equipo v ON v.id_equipo = p.id_equipo_visitante "
        "JOIN turno t ON t.id_turno = p.id_turno "
        "JOIN complejo c ON c.id_complejo = p.id_complejo "
        "LEFT JOIN v_resultados r ON r.id_partido = p.id_partido "
        "WHERE p.id_torneo = %s "
        "ORDER BY p.numero_fecha, p.dia, t.hora_inicio",
        (id_torneo,),
    )

    for r in rows:
        r["puede_marcar_jugado"] = (
            r["estado"] in ("programado", "postergado")
            and can_mark_match_played(r["dia"], r["hora_fin"])
        )
        r["en_plazo_correccion"] = (
            r["estado"] == "jugado"
            and is_within_correction_window(r["dia"], r["hora_fin"])
        )

    teams = []
    courts = []
    shifts = query("SELECT * FROM turno ORDER BY hora_inicio")

    if current_torneo:
        teams = query(
            "SELECT e.id_equipo, e.nombre, COUNT(ej.ci_jugador) AS jugadores "
            "FROM equipo e "
            "LEFT JOIN equipo_jugador_torneo ej "
            "  ON ej.id_equipo = e.id_equipo AND ej.id_torneo = e.id_torneo "
            "WHERE e.id_torneo = %s "
            "GROUP BY e.id_equipo, e.nombre "
            "ORDER BY e.nombre",
            (id_torneo,),
        )
        courts = query(
            "SELECT ca.nombre_cancha, ca.id_complejo, ca.superficie, "
            "co.nombre AS complejo_nombre "
            "FROM cancha ca "
            "JOIN complejo co ON co.id_complejo = ca.id_complejo "
            "ORDER BY co.nombre, ca.nombre_cancha"
        )

    return render_template(
        "fixture.html",
        title="Fixture y Gestión de Partidos",
        tournaments=tournaments,
        current_torneo=current_torneo,
        rows=rows,
        teams=teams,
        courts=courts,
        shifts=shifts,
        states=ESTADOS_PARTIDO,
    )


@partidos_bp.post("/partidos/crear")
@required(admin=True)
def create_match():
    id_torneo_fallback = request.form.get("id_torneo", "1")
    try:
        match_data = validate_match_form({**request.form, "estado": "programado"})
        transaction(lambda cur: _execute_match_write_saga(cur, match_data))
        flash("Partido programado correctamente.", "ok")
    except ValueError as e:
        flash(str(e), "error")
    except mysql.connector.Error as e:
        flash(getattr(e, "msg", "No se pudo programar el partido."), "error")
    return redirect(url_for("fixture", torneo=id_torneo_fallback))


@partidos_bp.route("/partidos/<int:id_partido>/editar", methods=["GET", "POST"])
@required(admin=True)
def edit_match(id_partido):
    rows = query(
        "SELECT p.*, t.hora_inicio, t.hora_fin "
        "FROM partido p JOIN turno t ON t.id_turno = p.id_turno "
        "WHERE p.id_partido = %s",
        (id_partido,),
    )
    if not rows:
        flash("Partido no encontrado.", "error")
        return redirect(url_for("fixture"))
    match = rows[0]

    if request.method == "POST":
        try:
            form_payload = {
                **request.form,
                "id_torneo": match["id_torneo"],
                "estado": request.form.get("estado", match["estado"]),
            }
            match_data = validate_match_form(form_payload)
            transaction(
                lambda cur: _execute_match_write_saga(
                    cur, match_data, editing_id=id_partido
                )
            )
            flash("Partido actualizado / reprogramado correctamente.", "ok")
            return redirect(url_for("fixture", torneo=match["id_torneo"]))
        except ValueError as e:
            flash(str(e), "error")
        except mysql.connector.Error as e:
            flash(getattr(e, "msg", "No se pudo actualizar el partido."), "error")

    torneo = query("SELECT * FROM torneo WHERE id_torneo=%s", (match["id_torneo"],))[0]
    teams = query(
        "SELECT e.id_equipo, e.nombre, COUNT(ej.ci_jugador) AS jugadores "
        "FROM equipo e "
        "LEFT JOIN equipo_jugador_torneo ej "
        "  ON ej.id_equipo = e.id_equipo AND ej.id_torneo = e.id_torneo "
        "WHERE e.id_torneo = %s "
        "GROUP BY e.id_equipo, e.nombre ORDER BY e.nombre",
        (match["id_torneo"],),
    )
    courts = query(
        "SELECT ca.nombre_cancha, ca.id_complejo, co.nombre AS complejo_nombre "
        "FROM cancha ca JOIN complejo co ON co.id_complejo = ca.id_complejo "
        "ORDER BY co.nombre, ca.nombre_cancha"
    )
    shifts = query("SELECT * FROM turno ORDER BY hora_inicio")

    return render_template(
        "edit_match.html",
        title=f"Modificar / Reprogramar Partido #{id_partido}",
        match=match,
        torneo=torneo,
        teams=teams,
        courts=courts,
        shifts=shifts,
        states=ESTADOS_PARTIDO,
        en_plazo_correccion=(
            match["estado"] != "jugado"
            or is_within_correction_window(match["dia"], match["hora_fin"])
        ),
    )


@partidos_bp.post("/partidos/<int:id_partido>/estado")
@required(admin=True)
def change_match_state(id_partido):
    nuevo_estado = request.form.get("estado", "").strip()
    id_torneo_redirect = request.form.get("id_torneo", "1")

    if nuevo_estado not in ESTADOS_PARTIDO:
        flash("Estado de partido inválido.", "error")
        return redirect(url_for("fixture", torneo=id_torneo_redirect))

    def op(cur):
        cur.execute(
            "SELECT p.*, t.hora_fin, tor.estado AS estado_torneo, "
            "tor.fecha_inicio, tor.fecha_fin "
            "FROM partido p "
            "JOIN turno t ON t.id_turno = p.id_turno "
            "JOIN torneo tor ON tor.id_torneo = p.id_torneo "
            "WHERE p.id_partido = %s FOR UPDATE",
            (id_partido,),
        )
        m = cur.fetchone()
        if not m:
            raise ValueError("Partido no encontrado.")
        if m["estado_torneo"] == "finalizado":
            raise ValueError("No se pueden cambiar estados en una edición finalizada.")

        if m["estado"] == "jugado" and nuevo_estado != "jugado":
            validate_correction_window(m["dia"], m["hora_fin"])

        if nuevo_estado == "jugado":
            if not can_mark_match_played(m["dia"], m["hora_fin"]):
                raise ValueError(
                    "Solo se puede marcar un partido como jugado después de finalizar su turno."
                )

        if m["estado"] == "cancelado" and nuevo_estado != "cancelado":
            match_data = {
                "id_torneo": m["id_torneo"],
                "numero_fecha": m["numero_fecha"],
                "id_equipo_local": m["id_equipo_local"],
                "id_equipo_visitante": m["id_equipo_visitante"],
                "dia": str(m["dia"]),
                "id_turno": m["id_turno"],
                "nombre_cancha": m["nombre_cancha"],
                "id_complejo": m["id_complejo"],
                "estado": nuevo_estado,
            }
            _execute_match_write_saga(cur, match_data, editing_id=id_partido)
            return

        cur.execute(
            "UPDATE partido SET estado=%s WHERE id_partido=%s",
            (nuevo_estado, id_partido),
        )

    try:
        transaction(op)
        flash(f"Estado del partido actualizado a '{nuevo_estado}'.", "ok")
    except ValueError as e:
        flash(str(e), "error")
    except mysql.connector.Error as e:
        flash(getattr(e, "msg", "No se pudo cambiar el estado del partido."), "error")

    return redirect(url_for("fixture", torneo=id_torneo_redirect))


@partidos_bp.post("/partidos/<int:id_partido>/eliminar")
@required(admin=True)
def delete_match(id_partido):
    id_torneo_redirect = request.form.get("id_torneo", "1")

    def op(cur):
        cur.execute(
            "SELECT id_partido, id_torneo, estado FROM partido WHERE id_partido=%s FOR UPDATE",
            (id_partido,),
        )
        m = cur.fetchone()
        if not m:
            raise ValueError("El partido no existe.")
        if m["estado"] == "jugado":
            raise ValueError("No se permite eliminar un partido jugado.")
        cur.execute("DELETE FROM partido WHERE id_partido=%s", (id_partido,))

    try:
        transaction(op)
        flash("Partido eliminado.", "ok")
    except ValueError as e:
        flash(str(e), "error")
    except mysql.connector.Error:
        flash(
            "No se puede eliminar el partido (está jugado o tiene planillas asociadas).",
            "error",
        )

    return redirect(url_for("fixture", torneo=id_torneo_redirect))