import re
from datetime import date

TIPOS = ("grado", "posgrado", "docente", "funcionario")


def validate_player(data):
    fields = (
        "ci",
        "nombre",
        "apellido",
        "email",
        "fecha_nacimiento",
        "id_facultad",
        "tipo",
    )
    values = {k: str(data.get(k, "")).strip() for k in fields}
    if not re.fullmatch(r"[0-9]{6,12}", values["ci"]):
        raise ValueError("CI: entre 6 y 12 digitos, sin separadores.")
    if any(not values[k] or len(values[k]) > 80 for k in ("nombre", "apellido")):
        raise ValueError("Nombre y apellido: entre 1 y 80 caracteres.")
    if len(values["email"]) > 254 or not re.fullmatch(
        r"[^ @]+@[^ @]+[.][^ @]+", values["email"]
    ):
        raise ValueError("Correo invalido.")
    try:
        birth = date.fromisoformat(values["fecha_nacimiento"])
        faculty = int(values["id_facultad"])
    except ValueError:
        raise ValueError("Fecha o facultad invalida.")
    if birth > date.today():
        raise ValueError("La fecha no puede ser futura.")
    if faculty < 1 or values["tipo"] not in TIPOS:
        raise ValueError("Facultad o tipo invalido.")
    return tuple(values[k] for k in fields)
def validate_team(data):
    fields = ('nombre', 'id_torneo', 'id_facultad', 'ci_capitan')
    values = {k: str(data.get(k, '')).strip() for k in fields}

    if not values['nombre'] or len(values['nombre']) > 100:
        raise ValueError('Nombre de equipo: entre 1 y 100 caracteres.')

    for k in ('id_torneo', 'id_facultad'):
        if not re.fullmatch(r'[1-9][0-9]*', values[k]):
            raise ValueError('Torneo y facultad deben ser identificadores válidos.')
        values[k] = int(values[k])

    if not values['ci_capitan']:
        values['ci_capitan'] = None
    elif not re.fullmatch(r'[0-9]{6,12}', values['ci_capitan']):
        raise ValueError('CI del capitán: entre 6 y 12 dígitos, sin separadores.')

    return (
        values['nombre'],
        values['id_torneo'],
        values['id_facultad'],
        values['ci_capitan']
    )
def validate_complex(data):
    nombre = data.get('nombre', '').strip()
    direccion = data.get('direccion', '').strip()
    departamento = data.get('departamento', '').strip()

    if not nombre or not direccion or not departamento:
        raise ValueError('Todos los campos son obligatorios.')

    if len(nombre) > 100:
        raise ValueError('El nombre no puede superar los 100 caracteres.')

    if len(direccion) > 200:
        raise ValueError('La dirección no puede superar los 200 caracteres.')

    if len(departamento) > 80:
        raise ValueError('El departamento no puede superar los 80 caracteres.')

    for campo, valor in (
        ('nombre', nombre),
        ('dirección', direccion),
        ('departamento', departamento)
    ):
        if any(ord(c) < 32 or ord(c) == 127 for c in valor):
            raise ValueError(f'El campo {campo} contiene caracteres no permitidos.')

        if not any(c.isalnum() for c in valor):
            raise ValueError(f'El campo {campo} debe contener letras o números.')

    return nombre, direccion, departamento

def validate_court(data):
    nombre = data.get('nombre_cancha', '').strip()
    superficie = data.get('superficie', '').strip()
    techada = data.get('techada', '').strip()

    if not nombre:
        raise ValueError('El nombre de la cancha es obligatorio.')

    if len(nombre) > 80:
        raise ValueError('El nombre no puede superar los 80 caracteres.')

    if any(ord(c) < 32 or ord(c) == 127 for c in nombre):
        raise ValueError('El nombre contiene caracteres no permitidos.')

    if not any(c.isalnum() for c in nombre):
        raise ValueError('El nombre debe contener letras o números.')
    if techada not in ('0', '1'):
        raise ValueError('Debes indicar si la cancha es techada.')

    if superficie == 'sintetico':
        superficie = 'sintÃ©tico'
    elif superficie != 'parquet':
        raise ValueError('La superficie seleccionada no es válida.')
    return nombre, superficie, int(techada)

def validate_ci(value):
    ci = str(value).strip()

    if not re.fullmatch(r'[0-9]{6,12}', ci):
        raise ValueError('CI: entre 6 y 12 dígitos, sin separadores.')

    return ci


def validate_minute(value):
    minute = str(value).strip()

    if not re.fullmatch(r'[0-9]+', minute):
        raise ValueError('El minuto debe ser un número entero.')

    minute = int(minute)

    if not 0 <= minute <= 60:
        raise ValueError('El minuto debe estar entre 0 y 60.')

    return minute


def validate_card_color(value):
    color = str(value).strip()

    if color not in ('amarilla', 'roja'):
        raise ValueError('El tipo de tarjeta no es válido.')

    return color
def validate_matchday(value):
    value = str(value).strip()

    if not re.fullmatch(r'[1-9][0-9]*', value):
        raise ValueError('La fecha debe ser un número entero mayor que cero.')

    value = int(value)

    if value > 2147483647:
        raise ValueError('La fecha supera el máximo permitido.')

    return value


def validate_suspension(value):
    value = str(value).strip()

    if not re.fullmatch(r'[1-9][0-9]*', value):
        raise ValueError(
            'La cantidad de fechas debe ser un número entero mayor que cero.'
        )

    value = int(value)

    if value > 2147483647:
        raise ValueError('La cantidad de fechas supera el máximo permitido.')

    return value