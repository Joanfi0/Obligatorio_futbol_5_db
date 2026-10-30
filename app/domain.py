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
