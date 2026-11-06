
from datetime import date

import mysql.connector
from flask import Blueprint, render_template, request, redirect, url_for, flash

from .web import query, required
from .domain import validate_player, TIPOS


jugadores_bp = Blueprint('jugadores', __name__)


@jugadores_bp.route('/jugadores', methods=['GET', 'POST'])
@required(admin=True)
def players():

    if request.method == 'POST':
        try:
            vals = validate_player(request.form)

            query(
                'INSERT INTO jugador (ci,nombre,apellido,email,fecha_nacimiento,id_facultad,tipo) VALUES (%s,%s,%s,%s,%s,%s,%s)',
                vals,
                write=True
            )

            flash('Jugador creado. Aún no integra un plantel.', 'ok')
            return redirect(url_for('jugadores.players'))

        except ValueError as e:
            flash(str(e), 'error')

        except mysql.connector.Error:
            flash('No se pudo guardar. Verifica CI y correo únicos, facultad y fecha.', 'error')

    return render_template(
        'players.html',
        title='Jugadores',
        rows=query('SELECT * FROM jugador ORDER BY apellido,nombre'),
        faculties=query('SELECT * FROM facultad'),
        types=TIPOS,
        player=request.form if request.method == 'POST' else {},
        editing=False,
        today=date.today().isoformat()
    )


# EDITAR JUGADOR
@jugadores_bp.route('/jugadores/<ci>/editar', methods=['GET', 'POST'])
@required(admin=True)
def edit_player(ci):

    rows = query(
        'SELECT * FROM jugador WHERE ci=%s',
        (ci,)
    )

    if not rows:
        from flask import abort
        abort(404)

    if request.method == 'POST':
        try:
            data = request.form.to_dict()
            data['ci'] = ci

            vals = validate_player(data)

            query(
                'UPDATE jugador SET nombre=%s,apellido=%s,email=%s,fecha_nacimiento=%s,id_facultad=%s,tipo=%s WHERE ci=%s',
                vals[1:] + (ci,),
                write=True
            )

            flash('Jugador actualizado.', 'ok')
            return redirect(url_for('jugadores.players'))

        except ValueError as e:
            flash(str(e), 'error')

        except mysql.connector.Error:
            flash('No se pudo actualizar. Un jugador inscripto conserva facultad y tipo; el correo debe ser único.', 'error')

    return render_template(
        'players.html',
        title='Editar jugador',
        rows=[],
        faculties=query('SELECT * FROM facultad'),
        types=TIPOS,
        player=request.form if request.method == 'POST' else rows[0],
        editing=True,
        today=date.today().isoformat()
    )


# ELIMINAR JUGADOR
@jugadores_bp.post('/jugadores/<ci>/eliminar')
@required(admin=True)
def delete_player(ci):

    try:
        query(
            'DELETE FROM jugador WHERE ci=%s',
            (ci,),
            write=True
        )

        flash('Baja procesada.', 'ok')

    except mysql.connector.Error:
        flash('No se puede eliminar: existen referencias (plantel, capitanía o historial).', 'error')

    return redirect(url_for('jugadores.players'))
