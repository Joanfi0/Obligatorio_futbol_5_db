import mysql.connector
from flask import Blueprint, render_template, request, redirect, url_for, flash

from .web import query, required
from .domain import validate_court


canchas_bp = Blueprint('canchas', __name__)


@canchas_bp.route('/complejos/<int:id_complejo>/canchas', methods=['GET', 'POST'])
@required(admin=True)
def courts(id_complejo):
    complex_rows = query(
        'SELECT * FROM complejo WHERE id_complejo=%s',
        (id_complejo,)
    )

    if not complex_rows:
        flash('Complejo no encontrado.', 'error')
        return redirect(url_for('complejos.complexes'))

    complex_data = complex_rows[0]

    if request.method == 'POST':
        try:
            vals = validate_court(request.form)

            query(
                'INSERT INTO cancha (nombre_cancha, id_complejo, superficie, techada) '
                'VALUES (%s, %s, %s, %s)',
                (vals[0], id_complejo, vals[1], vals[2]),
                write=True
            )

            flash('Cancha creada correctamente.', 'ok')

        except ValueError as e:
            flash(str(e), 'error')

        except mysql.connector.IntegrityError as e:
            if e.errno == 1062:
                flash('Ya existe una cancha con ese nombre en este complejo.', 'error')
            else:
                flash('No se pudo crear la cancha por un error de integridad.', 'error')

        except mysql.connector.Error as e:
            print('ERROR MYSQL AL CREAR CANCHA:', repr(e))
            flash(f'No se pudo guardar la cancha: {e.msg}', 'error')
        return redirect(url_for('canchas.courts', id_complejo=id_complejo))

    return render_template(
        'courts.html',
        title='Canchas',
        complex=complex_data,
        rows=query(
            'SELECT * FROM cancha WHERE id_complejo=%s ORDER BY nombre_cancha',
            (id_complejo,)
        ),
        editing=False
    )


@canchas_bp.route(
    '/complejos/<int:id_complejo>/canchas/editar',
    methods=['GET', 'POST']
)
@required(admin=True)
def edit_court(id_complejo):
    complex_rows = query(
        'SELECT * FROM complejo WHERE id_complejo=%s',
        (id_complejo,)
    )

    if not complex_rows:
        flash('Complejo no encontrado.', 'error')
        return redirect(url_for('complejos.complexes'))

    complex_data = complex_rows[0]

    nombre_original = (
        request.form.get('nombre_original', '')
        if request.method == 'POST'
        else request.args.get('nombre_cancha', '')
    )

    result = query(
        'SELECT * FROM cancha '
        'WHERE id_complejo=%s AND nombre_cancha=%s',
        (id_complejo, nombre_original)
    )

    if not result:
        flash('Cancha no encontrada.', 'error')
        return redirect(url_for('canchas.courts', id_complejo=id_complejo))

    court_data = result[0]

    if request.method == 'POST':
        try:
            vals = validate_court(request.form)

            query(
                'UPDATE cancha SET nombre_cancha=%s, superficie=%s, techada=%s '
                'WHERE id_complejo=%s AND nombre_cancha=%s',
                (vals[0], vals[1], vals[2], id_complejo, nombre_original),
                write=True
            )

            flash('Cancha actualizada.', 'ok')
            return redirect(url_for('canchas.courts', id_complejo=id_complejo))

        except ValueError as e:
            flash(str(e), 'error')
            court_data = request.form

        except mysql.connector.IntegrityError as e:
            if e.errno == 1062:
                flash('Ya existe una cancha con ese nombre en este complejo.', 'error')
            else:
                flash('No se pudo actualizar la cancha por un error de integridad.', 'error')

            court_data = request.form

        except mysql.connector.Error as e:
            print('ERROR MYSQL AL ACTUALIZAR CANCHA:', repr(e))
            flash('No se pudo actualizar la cancha.', 'error')
            court_data = request.form

    return render_template(
        'courts.html',
        title='Editar cancha',
        complex=complex_data,
        court=court_data,
        nombre_original=nombre_original,
        rows=query(
            'SELECT * FROM cancha WHERE id_complejo=%s ORDER BY nombre_cancha',
            (id_complejo,)
        ),
        editing=True
    )


@canchas_bp.post('/complejos/<int:id_complejo>/canchas/eliminar')
@required(admin=True)
def delete_court(id_complejo):
    nombre_cancha = request.form.get('nombre_cancha', '').strip()

    try:
        query(
            'DELETE FROM cancha '
            'WHERE id_complejo=%s AND nombre_cancha=%s',
            (id_complejo, nombre_cancha),
            write=True
        )

        flash('Cancha eliminada.', 'ok')

    except mysql.connector.Error as e:
        print('ERROR MYSQL AL ELIMINAR CANCHA:', repr(e))
        flash('No se pudo eliminar la cancha.', 'error')

    return redirect(url_for('canchas.courts', id_complejo=id_complejo))