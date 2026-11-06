
import re

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

from .web import query, transaction, required


planteles_bp = Blueprint('planteles', __name__)


@planteles_bp.get('/equipos/<int:id_equipo>/plantel')
@required(admin=True)
def roster(id_equipo):
    teams = query(
        'SELECT e.id_equipo, e.nombre, e.id_torneo, e.id_facultad, '
        'e.ci_capitan, t.nombre torneo, t.anio, t.semestre, t.estado '
        'FROM equipo e '
        'JOIN torneo t ON t.id_torneo=e.id_torneo '
        'WHERE e.id_equipo=%s',
        (id_equipo,)
    )

    if not teams:
        abort(404)

    team = teams[0]

    members = query(
        'SELECT j.ci, j.nombre, j.apellido, j.tipo, '
        'ej.numero_camiseta, '
        'CASE WHEN e.ci_capitan=j.ci THEN 1 ELSE 0 END AS es_capitan '
        'FROM equipo_jugador_torneo ej '
        'JOIN jugador j ON j.ci=ej.ci_jugador '
        'JOIN equipo e ON e.id_equipo=ej.id_equipo '
        'AND e.id_torneo=ej.id_torneo '
        'WHERE ej.id_equipo=%s '
        'ORDER BY ej.numero_camiseta',
        (id_equipo,)
    )

    available = query(
        'SELECT j.ci, j.nombre, j.apellido, j.tipo '
        'FROM jugador j '
        'WHERE j.id_facultad=%s '
        'AND NOT EXISTS ('
        '    SELECT 1 FROM equipo_jugador_torneo ej '
        '    WHERE ej.ci_jugador=j.ci AND ej.id_torneo=%s'
        ') '
        'ORDER BY j.apellido, j.nombre',
        (team['id_facultad'], team['id_torneo'])
    )

    return render_template(
        'rosters.html',
        title='Plantel',
        team=team,
        members=members,
        available=available,
        total=len(members),
        staff=sum(
            1 for member in members
            if member['tipo'] in ('docente', 'funcionario')
        )
    )


@planteles_bp.post('/equipos/<int:id_equipo>/plantel/agregar')
@required(admin=True)
def add_member(id_equipo):
    ci = request.form.get('ci', '').strip()
    camiseta = request.form.get('numero_camiseta', '').strip()

    if not re.fullmatch(r'[0-9]{6,12}', ci):
        flash('La CI debe tener entre 6 y 12 dígitos.', 'error')
        return redirect(url_for('planteles.roster', id_equipo=id_equipo))

    if not re.fullmatch(r'[0-9]{1,2}', camiseta):
        flash('El número de camiseta debe estar entre 1 y 99.', 'error')
        return redirect(url_for('planteles.roster', id_equipo=id_equipo))

    camiseta = int(camiseta)

    if not 1 <= camiseta <= 99:
        flash('El número de camiseta debe estar entre 1 y 99.', 'error')
        return redirect(url_for('planteles.roster', id_equipo=id_equipo))

    def operation(cur):
        cur.execute(
            'SELECT e.id_equipo, e.id_torneo, e.id_facultad, t.estado '
            'FROM equipo e '
            'JOIN torneo t ON t.id_torneo=e.id_torneo '
            'WHERE e.id_equipo=%s FOR UPDATE',
            (id_equipo,)
        )
        team = cur.fetchone()

        if not team:
            raise ValueError('El equipo no existe.')

        if team['estado'] != 'inscripciÃ³n':
            raise ValueError('El plantel solo puede modificarse durante la inscripción.')

        cur.execute(
            'SELECT ci, id_facultad, tipo '
            'FROM jugador WHERE ci=%s',
            (ci,)
        )
        player = cur.fetchone()

        if not player:
            raise ValueError('No existe un jugador con esa CI.')

        if player['id_facultad'] != team['id_facultad']:
            raise ValueError('El jugador debe pertenecer a la misma facultad que el equipo.')

        cur.execute(
            'SELECT COUNT(*) total, '
            "SUM(j.tipo IN ('docente','funcionario')) docentes "
            'FROM equipo_jugador_torneo ej '
            'JOIN jugador j ON j.ci=ej.ci_jugador '
            'WHERE ej.id_equipo=%s AND ej.id_torneo=%s',
            (id_equipo, team['id_torneo'])
        )
        counts = cur.fetchone()

        if counts['total'] >= 10:
            raise ValueError('El plantel no puede superar los 10 integrantes.')

        if player['tipo'] in ('docente', 'funcionario') and (counts['docentes'] or 0) >= 2:
            raise ValueError('El plantel no puede tener más de 2 docentes o funcionarios.')

        cur.execute(
            'SELECT id_equipo FROM equipo_jugador_torneo '
            'WHERE ci_jugador=%s AND id_torneo=%s',
            (ci, team['id_torneo'])
        )

        if cur.fetchone():
            raise ValueError('El jugador ya integra un equipo de esta edición.')

        cur.execute(
            'INSERT INTO equipo_jugador_torneo '
            '(id_equipo, ci_jugador, id_torneo, numero_camiseta) '
            'VALUES (%s, %s, %s, %s)',
            (id_equipo, ci, team['id_torneo'], camiseta)
        )

    try:
        transaction(operation)
        flash('Jugador agregado al plantel.', 'ok')

    except ValueError as e:
        flash(str(e), 'error')

    except mysql.connector.Error as e:
        if e.errno == 1062:
            flash('El jugador ya está inscripto o el número de camiseta está ocupado.', 'error')
        else:
            raise

    return redirect(url_for('planteles.roster', id_equipo=id_equipo))


@planteles_bp.post('/equipos/<int:id_equipo>/plantel/capitan')
@required(admin=True)
def set_captain(id_equipo):
    ci = request.form.get('ci_capitan', '').strip()

    if ci and not re.fullmatch(r'[0-9]{6,12}', ci):
        flash('La CI del capitán no es válida.', 'error')
        return redirect(url_for('planteles.roster', id_equipo=id_equipo))

    def operation(cur):
        cur.execute(
            'SELECT e.id_equipo, e.id_torneo, t.estado '
            'FROM equipo e '
            'JOIN torneo t ON t.id_torneo=e.id_torneo '
            'WHERE e.id_equipo=%s FOR UPDATE',
            (id_equipo,)
        )
        team = cur.fetchone()

        if not team:
            raise ValueError('El equipo no existe.')

        if team['estado'] != 'inscripciÃ³n':
            raise ValueError('El capitán solo puede modificarse durante la inscripción.')

        if ci:
            cur.execute(
                'SELECT ci_jugador FROM equipo_jugador_torneo '
                'WHERE id_equipo=%s AND id_torneo=%s AND ci_jugador=%s',
                (id_equipo, team['id_torneo'], ci)
            )

            if not cur.fetchone():
                raise ValueError('El capitán debe pertenecer al plantel.')

        cur.execute(
            'UPDATE equipo SET ci_capitan=%s WHERE id_equipo=%s',
            (ci or None, id_equipo)
        )

    try:
        transaction(operation)
        flash('Capitán actualizado.', 'ok')

    except ValueError as e:
        flash(str(e), 'error')

    return redirect(url_for('planteles.roster', id_equipo=id_equipo))
@planteles_bp.post('/equipos/<int:id_equipo>/plantel/quitar')
@required(admin=True)
def remove_member(id_equipo):
    ci = request.form.get('ci', '').strip()

    if not re.fullmatch(r'[0-9]{6,12}', ci):
        flash('La CI del jugador no es válida.', 'error')
        return redirect(url_for('planteles.roster', id_equipo=id_equipo))

    def operation(cur):
        cur.execute(
            'SELECT e.id_equipo, e.id_torneo, e.ci_capitan, t.estado '
            'FROM equipo e '
            'JOIN torneo t ON t.id_torneo=e.id_torneo '
            'WHERE e.id_equipo=%s FOR UPDATE',
            (id_equipo,)
        )
        team = cur.fetchone()

        if not team:
            raise ValueError('El equipo no existe.')

        if team['estado'] != 'inscripciÃ³n':
            raise ValueError('El plantel solo puede modificarse durante la inscripción.')

        cur.execute(
            'SELECT ci_jugador FROM equipo_jugador_torneo '
            'WHERE id_equipo=%s AND id_torneo=%s AND ci_jugador=%s',
            (id_equipo, team['id_torneo'], ci)
        )

        if not cur.fetchone():
            raise ValueError('El jugador no integra este plantel.')

        if team['ci_capitan'] == ci:
            cur.execute(
                'UPDATE equipo SET ci_capitan=NULL '
                'WHERE id_equipo=%s',
                (id_equipo,)
            )

        cur.execute(
            'DELETE FROM equipo_jugador_torneo '
            'WHERE id_equipo=%s AND id_torneo=%s AND ci_jugador=%s',
            (id_equipo, team['id_torneo'], ci)
        )

    try:
        transaction(operation)
        flash('Jugador quitado del plantel.', 'ok')

    except ValueError as e:
        flash(str(e), 'error')

    return redirect(url_for('planteles.roster', id_equipo=id_equipo))
