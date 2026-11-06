from datetime import date

import mysql.connector
from flask import Blueprint, render_template, request, redirect, url_for, flash

from .web import query, required
from .domain import validate_team, TIPOS


equipos_bp = Blueprint('equipos', __name__)

@equipos_bp.route('/equipos', methods=['GET', 'POST'])
@required(admin=True)
def teams():
    if request.method == 'POST':
        try:
            vals = validate_team(request.form)

            query(
                'INSERT INTO equipo (nombre,id_torneo,id_facultad,ci_capitan) VALUES (%s,%s,%s,%s)',
                vals,
                write=True
            )

            flash('Equipo creado.', 'ok')
            return redirect(url_for('equipos.teams'))

        except ValueError as e:
            flash(str(e), 'error')

        except mysql.connector.Error as e:
            print('ERROR MYSQL:', repr(e))
            flash('No se pudo guardar. Verifica los datos ingresados.', 'error')
    return render_template(
        'teams.html',
        tournaments=query('SELECT * FROM torneo ORDER BY anio DESC,semestre DESC'),
        title='Equipos',
        rows=query('SELECT * FROM equipo ORDER BY nombre'),
        faculties=query('SELECT * FROM facultad'),
        types=TIPOS,
        team=request.form if request.method == 'POST' else {},
        editing=False
        
    )
@equipos_bp.route('/equipos/<int:id_equipo>/editar', methods=['GET', 'POST'])
@required(admin=True)
def edit_team(id_equipo):
    team = query(
        'SELECT * FROM equipo WHERE id_equipo=%s',
        (id_equipo,)
    )

    if not team:
        flash('Equipo no encontrado.', 'error')
        return redirect(url_for('equipos.teams'))

    team = team[0]

    if request.method == 'POST':
        try:
            vals = validate_team(request.form)

            query(
                'UPDATE equipo SET nombre=%s, id_torneo=%s, id_facultad=%s, ci_capitan=%s WHERE id_equipo=%s',
                vals + (id_equipo,),
                write=True
            )

            flash('Equipo actualizado.', 'ok')
            return redirect(url_for('equipos.teams'))

        except ValueError as e:
            flash(str(e), 'error')
            team = request.form

        except mysql.connector.Error as e:
            print('ERROR MYSQL AL ACTUALIZAR EQUIPO:', repr(e))
            flash('No se pudo actualizar. Verifica que el nombre sea único, la facultad y el capitán.', 'error')
            team = request.form
    return render_template(
        'teams.html',
        title='Editar equipo',
        rows=query('SELECT * FROM equipo ORDER BY nombre'),
        faculties=query('SELECT * FROM facultad'),
        tournaments=query('SELECT * FROM torneo ORDER BY anio DESC,semestre DESC'),
        types=TIPOS,
        team=team,
        editing=True,
        edit_id=id_equipo
    )
@equipos_bp.post('/equipos/<int:id_equipo>/eliminar')
@required(admin=True)
def delete_team(id_equipo):
    try:
        query(
            'DELETE FROM equipo WHERE id_equipo=%s',
            (id_equipo,),
            write=True
        )

        flash('Equipo eliminado.', 'ok')

    except mysql.connector.Error as e:
        print('ERROR MYSQL AL ELIMINAR EQUIPO:', repr(e))
        flash('No se pudo eliminar el equipo. Puede tener registros asociados.', 'error')

    return redirect(url_for('equipos.teams'))