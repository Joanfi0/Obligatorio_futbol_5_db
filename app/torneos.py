import mysql.connector
from flask import Blueprint, render_template, request, redirect, url_for, flash
from .web import query, transaction, required
from .domain import (
    ESTADOS_TORNEO,
    validate_tournament,
    validate_tournament_transition,
)

torneos_bp = Blueprint("torneos", __name__)


@torneos_bp.route("/torneos", methods=["GET", "POST"])
@required(admin=True)
def tournaments():
    if request.method == "POST":
        try:
            vals = validate_tournament({**request.form, "estado": "inscripcion"})
            query(
                "INSERT INTO torneo (nombre, anio, semestre, fecha_inicio, fecha_fin, estado) "
                "VALUES (%s, %s, %s, %s, %s, %s)",
                vals,
                write=True,
            )
            flash("Edición del torneo creada en estado de inscripción.", "ok")
            return redirect(url_for("torneos.tournaments"))
        except ValueError as e:
            flash(str(e), "error")
        except mysql.connector.IntegrityError as e:
            if e.errno == 1062:
                flash("Ya existe una edición registrada para ese año y semestre.", "error")
            else:
                flash("Error de integridad al crear la edición.", "error")
        except mysql.connector.Error:
            flash("No se pudo guardar la edición.", "error")

    rows = query(
        "SELECT t.*, "
        "(SELECT COUNT(*) FROM equipo e WHERE e.id_torneo = t.id_torneo) AS total_equipos, "
        "(SELECT COUNT(*) FROM partido p WHERE p.id_torneo = t.id_torneo) AS total_partidos "
        "FROM torneo t ORDER BY t.anio DESC, t.semestre DESC"
    )
    return render_template(
        "tournaments.html",
        title="Gestión de ediciones",
        rows=rows,
        states=ESTADOS_TORNEO,
        tournament=request.form if request.method == "POST" else {},
        editing=False,
    )


@torneos_bp.route("/torneos/<int:id_torneo>/editar", methods=["GET", "POST"])
@required(admin=True)
def edit_tournament(id_torneo):
    rows = query("SELECT * FROM torneo WHERE id_torneo=%s", (id_torneo,))
    if not rows:
        flash("Edición no encontrada.", "error")
        return redirect(url_for("torneos.tournaments"))
    current = rows[0]

    if request.method == "POST":
        try:
            vals = validate_tournament(
                {**request.form, "estado": current["estado"]}
            )

            def op(cur):
                cur.execute(
                    "SELECT * FROM torneo WHERE id_torneo=%s FOR UPDATE",
                    (id_torneo,),
                )
                tor = cur.fetchone()
                if not tor:
                    raise ValueError("Edición no encontrada.")
                if tor["estado"] == "finalizado":
                    raise ValueError("No se puede modificar una edición finalizada.")

                cur.execute(
                    "SELECT MIN(dia) min_dia, MAX(dia) max_dia "
                    "FROM partido WHERE id_torneo=%s AND estado <> 'cancelado'",
                    (id_torneo,),
                )
                rango = cur.fetchone()
                if rango and rango["min_dia"]:
                    if str(vals[3]) > str(rango["min_dia"]) or str(vals[4]) < str(rango["max_dia"]):
                        raise ValueError(
                            "Las nuevas fechas dejan partidos activos fuera del rango de la edición."
                        )

                cur.execute(
                    "UPDATE torneo SET nombre=%s, anio=%s, semestre=%s, "
                    "fecha_inicio=%s, fecha_fin=%s WHERE id_torneo=%s",
                    (vals[0], vals[1], vals[2], vals[3], vals[4], id_torneo),
                )

            transaction(op)
            flash("Edición actualizada correctamente.", "ok")
            return redirect(url_for("torneos.tournaments"))
        except ValueError as e:
            flash(str(e), "error")
            current = request.form
        except mysql.connector.IntegrityError as e:
            if e.errno == 1062:
                flash("Ya existe otra edición en ese año y semestre.", "error")
            else:
                flash("Error de integridad al actualizar la edición.", "error")
            current = request.form

    all_rows = query(
        "SELECT t.*, "
        "(SELECT COUNT(*) FROM equipo e WHERE e.id_torneo = t.id_torneo) AS total_equipos, "
        "(SELECT COUNT(*) FROM partido p WHERE p.id_torneo = t.id_torneo) AS total_partidos "
        "FROM torneo t ORDER BY t.anio DESC, t.semestre DESC"
    )
    return render_template(
        "tournaments.html",
        title="Editar edición",
        rows=all_rows,
        states=ESTADOS_TORNEO,
        tournament=current,
        editing=True,
        edit_id=id_torneo,
    )


@torneos_bp.post("/torneos/<int:id_torneo>/estado")
@required(admin=True)
def change_state(id_torneo):
    nuevo_estado = request.form.get("estado", "").strip()

    def op(cur):
        cur.execute(
            "SELECT * FROM torneo WHERE id_torneo=%s FOR UPDATE",
            (id_torneo,),
        )
        tor = cur.fetchone()
        if not tor:
            raise ValueError("La edición no existe.")

        cur.execute(
            "SELECT e.id_equipo, e.nombre, COUNT(ej.ci_jugador) AS jugadores "
            "FROM equipo e "
            "LEFT JOIN equipo_jugador_torneo ej "
            "  ON ej.id_equipo = e.id_equipo AND ej.id_torneo = e.id_torneo "
            "WHERE e.id_torneo = %s "
            "GROUP BY e.id_equipo, e.nombre FOR UPDATE",
            (id_torneo,),
        )
        team_counts = cur.fetchall()

        cur.execute(
            "SELECT COUNT(*) AS pendientes FROM partido "
            "WHERE id_torneo = %s AND estado IN ('programado', 'postergado') FOR UPDATE",
            (id_torneo,),
        )
        pending = cur.fetchone()["pendientes"]

        if nuevo_estado == "en curso":
            cur.execute("SELECT e.nombre FROM equipo e LEFT JOIN equipo_jugador_torneo ej ON ej.id_equipo=e.id_equipo AND ej.id_torneo=e.id_torneo AND ej.ci_jugador=e.ci_capitan WHERE e.id_torneo=%s AND ej.ci_jugador IS NULL", (id_torneo,))
            if cur.fetchall():
                raise ValueError("Todos los equipos deben tener un capitán perteneciente al plantel.")
        if nuevo_estado == "finalizado":
            cur.execute("SELECT COUNT(*) total FROM equipo a JOIN equipo b ON a.id_torneo=b.id_torneo AND a.id_equipo<b.id_equipo WHERE a.id_torneo=%s AND NOT EXISTS (SELECT 1 FROM partido p WHERE p.id_torneo=a.id_torneo AND p.estado='jugado' AND LEAST(p.id_equipo_local,p.id_equipo_visitante)=a.id_equipo AND GREATEST(p.id_equipo_local,p.id_equipo_visitante)=b.id_equipo)", (id_torneo,))
            if cur.fetchone()["total"]:
                raise ValueError("Faltan enfrentamientos disputados para completar la liga de una rueda.")

        validate_tournament_transition(
            tor["estado"], nuevo_estado, team_counts, pending
        )

        cur.execute(
            "UPDATE torneo SET estado=%s WHERE id_torneo=%s",
            (nuevo_estado, id_torneo),
        )

    try:
        transaction(op)
        flash(f"Estado de la edición actualizado a '{nuevo_estado}'.", "ok")
    except ValueError as e:
        flash(str(e), "error")
    except mysql.connector.Error:
        flash("No se pudo cambiar el estado de la edición.", "error")

    return redirect(url_for("torneos.tournaments"))