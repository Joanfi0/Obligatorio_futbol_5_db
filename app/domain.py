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