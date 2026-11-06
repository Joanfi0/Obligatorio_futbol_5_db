
import mysql.connector
from flask import Blueprint, render_template, request, redirect, url_for, flash
from .domain import validate_complex
from .web import query, required


complejos_bp = Blueprint('complejos', __name__)

@complejos_bp.route('/complejos', methods=['GET', 'POST'])
@required(admin=True)
def complexes():
    if request.method == 'POST':
        try:
            vals = validate_complex(request.form)

            query(
                'INSERT INTO complejo (nombre, direccion, departamento) '
                'VALUES (%s, %s, %s)',
                vals,
                write=True
            )

            flash('Complejo creado.', 'ok')
            return redirect(url_for('complejos.complexes'))

        except ValueError as e:
            flash(str(e), 'error')

        except mysql.connector.Error as e:
            print('ERROR MYSQL AL CREAR COMPLEJO:', repr(e))
            flash('No se pudo guardar el complejo.', 'error')

    return render_template(
        'complex.html',
        title='Complejos deportivos',
        rows=query('SELECT * FROM complejo ORDER BY nombre'),
        complex=request.form if request.method == 'POST' else {},
        editing=False
    )


@complejos_bp.route('/complejos/<int:id_complejo>/editar', methods=['GET', 'POST'])
@required(admin=True)
def edit_complex(id_complejo):
    result = query(
        'SELECT * FROM complejo WHERE id_complejo=%s',
        (id_complejo,)
    )

    if not result:
        flash('Complejo no encontrado.', 'error')
        return redirect(url_for('complejos.complexes'))

    complex_data = result[0]

    if request.method == 'POST':
        try:
            vals = validate_complex(request.form)

            query(
                'UPDATE complejo SET nombre=%s, direccion=%s, departamento=%s '
                'WHERE id_complejo=%s',
                vals + (id_complejo,),
                write=True
            )

            flash('Complejo actualizado.', 'ok')
            return redirect(url_for('complejos.complexes'))

        except ValueError as e:
            flash(str(e), 'error')
            complex_data = request.form

        except mysql.connector.Error as e:
            print('ERROR MYSQL AL ACTUALIZAR COMPLEJO:', repr(e))
            flash('No se pudo actualizar el complejo.', 'error')
            complex_data = request.form

    return render_template(
        'complex.html',
        title='Editar complejo',
        rows=query('SELECT * FROM complejo ORDER BY nombre'),
        complex=complex_data,
        editing=True,
        edit_id=id_complejo
    )


@complejos_bp.post('/complejos/<int:id_complejo>/eliminar')
@required(admin=True)
def delete_complex(id_complejo):
    try:
        query(
            'DELETE FROM complejo WHERE id_complejo=%s',
            (id_complejo,),
            write=True
        )

        flash('Complejo eliminado.', 'ok')

    except mysql.connector.Error as e:
        print('ERROR MYSQL AL ELIMINAR COMPLEJO:', repr(e))
        flash(
            'No se pudo eliminar el complejo. Verifica que no tenga canchas asociadas.',
            'error'
        )

    return redirect(url_for('complejos.complexes'))
