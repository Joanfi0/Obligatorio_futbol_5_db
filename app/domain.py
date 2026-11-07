import re
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

TIPOS = ("grado", "posgrado", "docente", "funcionario")
ESTADOS_TORNEO = ("inscripcion", "en curso", "finalizado")
ESTADOS_PARTIDO = ("programado", "jugado", "postergado", "cancelado")
TZ_MONTEVIDEO = ZoneInfo("America/Montevideo")


def now_montevideo():
    return datetime.now(TZ_MONTEVIDEO).replace(tzinfo=None)


def parse_time_value(val):
    if isinstance(val, time):
        return val
    if isinstance(val, timedelta):
        total_seconds = int(val.total_seconds())
        hours, remainder = divmod(total_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return time(hours, minutes, seconds)
    return time.fromisoformat(str(val))


def parse_date_value(val):
    if isinstance(val, date) and not isinstance(val, datetime):
        return val
    return date.fromisoformat(str(val))


def shift_end_datetime(dia, hora_fin):
    return datetime.combine(parse_date_value(dia), parse_time_value(hora_fin))


def can_mark_match_played(dia, hora_fin, current_dt=None):
    now = current_dt or now_montevideo()
    return now >= shift_end_datetime(dia, hora_fin)


def is_within_correction_window(dia, hora_fin, current_dt=None):
    now = current_dt or now_montevideo()
    end_dt = shift_end_datetime(dia, hora_fin)
    return end_dt <= now <= (end_dt + timedelta(hours=48))


def validate_correction_window(dia, hora_fin, current_dt=None):
    now = current_dt or now_montevideo()
    end_dt = shift_end_datetime(dia, hora_fin)
    if now < end_dt:
        raise ValueError("El turno del partido aún no ha finalizado.")
    if now > end_dt + timedelta(hours=48):
        raise ValueError(
            "El plazo de corrección de 48 horas desde el fin del turno ha vencido."
        )
    return True


class SagaCoordinator:
    """Orquestador de pasos transaccionales con compensación inversa (Patrón Saga)."""

    def __init__(self):
        self.steps = []
        self.completed = []
        self.compensation_log = []

    def add_step(self, name, action, compensate=None):
        self.steps.append((name, action, compensate))
        return self

    def execute(self):
        self.completed.clear()
        self.compensation_log.clear()
        try:
            for name, action, compensate in self.steps:
                action()
                self.completed.append((name, compensate))
        except Exception as exc:
            for name, compensate in reversed(self.completed):
                if compensate:
                    try:
                        compensate()
                        self.compensation_log.append(f"compensado:{name}")
                    except Exception as comp_exc:
                        self.compensation_log.append(
                            f"error_compensando:{name}:{comp_exc}"
                        )
            raise exc


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
    fields = ("nombre", "id_torneo", "id_facultad", "ci_capitan")
    values = {k: str(data.get(k, "")).strip() for k in fields}
    if not values["nombre"] or len(values["nombre"]) > 100:
        raise ValueError("Nombre de equipo: entre 1 y 100 caracteres.")
    for k in ("id_torneo", "id_facultad"):
        if not re.fullmatch(r"[1-9][0-9]*", values[k]):
            raise ValueError("Torneo y facultad deben ser identificadores válidos.")
        values[k] = int(values[k])
    if not values["ci_capitan"]:
        values["ci_capitan"] = None
    elif not re.fullmatch(r"[0-9]{6,12}", values["ci_capitan"]):
        raise ValueError("CI del capitán: entre 6 y 12 dígitos, sin separadores.")
    return (
        values["nombre"],
        values["id_torneo"],
        values["id_facultad"],
        values["ci_capitan"],
    )


def validate_complex(data):
    nombre = data.get("nombre", "").strip()
    direccion = data.get("direccion", "").strip()
    departamento = data.get("departamento", "").strip()
    if not nombre or not direccion or not departamento:
        raise ValueError("Todos los campos son obligatorios.")
    if len(nombre) > 100:
        raise ValueError("El nombre no puede superar los 100 caracteres.")
    if len(direccion) > 200:
        raise ValueError("La dirección no puede superar los 200 caracteres.")
    if len(departamento) > 80:
        raise ValueError("El departamento no puede superar los 80 caracteres.")
    for campo, valor in (
        ("nombre", nombre),
        ("dirección", direccion),
        ("departamento", departamento),
    ):
        if any(ord(c) < 32 or ord(c) == 127 for c in valor):
            raise ValueError(f"El campo {campo} contiene caracteres no permitidos.")
        if not any(c.isalnum() for c in valor):
            raise ValueError(f"El campo {campo} debe contener letras o números.")
    return nombre, direccion, departamento


def validate_court(data):
    nombre = data.get("nombre_cancha", "").strip()
    superficie = data.get("superficie", "").strip()
    techada = data.get("techada", "").strip()
    if not nombre:
        raise ValueError("El nombre de la cancha es obligatorio.")
    if len(nombre) > 80:
        raise ValueError("El nombre no puede superar los 80 caracteres.")
    if any(ord(c) < 32 or ord(c) == 127 for c in nombre):
        raise ValueError("El nombre contiene caracteres no permitidos.")
    if not any(c.isalnum() for c in nombre):
<<<<<<< Torneos_fixture_partidos
        raise ValueError("El nombre debe contener letras o números.")
    if superficie not in ("sintetico", "parquet"):
        raise ValueError("La superficie seleccionada no es válida.")
    if techada not in ("0", "1"):
        raise ValueError("Debes indicar si la cancha es techada.")
    return nombre, superficie, int(techada)


def validate_tournament(data):
    nombre = str(data.get("nombre", "")).strip()
    anio_raw = str(data.get("anio", "")).strip()
    semestre_raw = str(data.get("semestre", "")).strip()
    inicio_raw = str(data.get("fecha_inicio", "")).strip()
    fin_raw = str(data.get("fecha_fin", "")).strip()
    estado = str(data.get("estado", "inscripcion")).strip() or "inscripcion"

    if not nombre or len(nombre) > 120:
        raise ValueError("Nombre de edición: entre 1 y 120 caracteres.")
    try:
        anio = int(anio_raw)
        semestre = int(semestre_raw)
    except ValueError:
        raise ValueError("Año y semestre deben ser numéricos.")
    if not (2000 <= anio <= 2100):
        raise ValueError("Año fuera de rango válido (2000-2100).")
    if semestre not in (1, 2):
        raise ValueError("El semestre debe ser 1 o 2.")
    try:
        fecha_inicio = date.fromisoformat(inicio_raw)
        fecha_fin = date.fromisoformat(fin_raw)
    except ValueError:
        raise ValueError("Fechas de inicio y fin inválidas.")
    if fecha_fin < fecha_inicio:
        raise ValueError("La fecha de fin no puede ser anterior a la fecha de inicio.")
    if estado not in ESTADOS_TORNEO:
        raise ValueError("Estado de edición inválido.")
    return nombre, anio, semestre, fecha_inicio.isoformat(), fecha_fin.isoformat(), estado


def validate_tournament_transition(current_state, new_state, team_counts=(), pending_matches=0):
    if new_state not in ESTADOS_TORNEO:
        raise ValueError("Estado de torneo inválido.")
    if current_state == new_state:
        return True
    allowed = {
        "inscripcion": ("en curso",),
        "en curso": ("finalizado",),
        "finalizado": (),
    }
    if new_state not in allowed.get(current_state, ()):
        raise ValueError(
            f"Transición de estado no permitida: '{current_state}' a '{new_state}'."
        )
    if current_state == "inscripcion" and new_state == "en curso":
        if len(team_counts) < 2:
            raise ValueError(
                "Se requieren al menos 2 equipos inscriptos para iniciar la edición."
            )
        invalid_teams = [t["nombre"] for t in team_counts if t["jugadores"] < 5]
        if invalid_teams:
            raise ValueError(
                "No se puede iniciar el torneo; hay equipos con menos de 5 jugadores: "
                + ", ".join(invalid_teams)
            )
    if current_state == "en curso" and new_state == "finalizado":
        if pending_matches > 0:
            raise ValueError(
                "No se puede finalizar la edición mientras existan partidos programados o postergados."
            )
    return True


def validate_match_form(data):
    try:
        id_torneo = int(str(data.get("id_torneo", "")).strip())
        numero_fecha = int(str(data.get("numero_fecha", "")).strip())
        id_local = int(str(data.get("id_equipo_local", "")).strip())
        id_visitante = int(str(data.get("id_equipo_visitante", "")).strip())
        id_turno = int(str(data.get("id_turno", "")).strip())
    except ValueError:
        raise ValueError("Torneo, fecha, equipos y turno deben ser números enteros válidos.")

    dia_raw = str(data.get("dia", "")).strip()
    try:
        dia_dt = date.fromisoformat(dia_raw)
    except ValueError:
        raise ValueError("El día del partido no tiene un formato de fecha válido.")

    cancha_raw = str(data.get("cancha_complejo", "")).strip()
    if "|" in cancha_raw:
        id_comp_str, nombre_cancha = cancha_raw.split("|", 1)
        try:
            id_complejo = int(id_comp_str)
        except ValueError:
            raise ValueError("Complejo inválido.")
        nombre_cancha = nombre_cancha.strip()
    else:
        try:
            id_complejo = int(str(data.get("id_complejo", "")).strip())
        except ValueError:
            raise ValueError("Complejo inválido.")
        nombre_cancha = str(data.get("nombre_cancha", "")).strip()

    if not nombre_cancha or id_complejo < 1:
        raise ValueError("Debe seleccionar una cancha y complejo válidos.")
    if id_torneo < 1 or numero_fecha < 1 or id_turno < 1:
        raise ValueError("La fecha del torneo y el turno deben ser mayores a cero.")
    if id_local == id_visitante:
        raise ValueError("Un equipo no puede jugar contra sí mismo.")

    estado = str(data.get("estado", "programado")).strip() or "programado"
    if estado not in ESTADOS_PARTIDO:
        raise ValueError("Estado de partido inválido.")

    return {
        "id_torneo": id_torneo,
        "numero_fecha": numero_fecha,
        "id_equipo_local": id_local,
        "id_equipo_visitante": id_visitante,
        "dia": dia_dt.isoformat(),
        "id_turno": id_turno,
        "nombre_cancha": nombre_cancha,
        "id_complejo": id_complejo,
        "estado": estado,
    }


def validate_match_rules(
    match_data,
    tournament,
    teams_by_id,
    roster_counts,
    existing_matches,
    shift_end_time,
    editing_match=None,
    current_dt=None,
):
    """Valida todas las reglas de negocio de Persona 2 para creación/modificación de partidos."""
    now = current_dt or now_montevideo()

    if not tournament:
        raise ValueError("La edición seleccionada no existe.")
    if tournament["estado"] == "finalizado":
        raise ValueError("No se pueden crear ni modificar partidos en una edición finalizada.")

    if editing_match and editing_match["estado"] == "jugado":
        old_end = editing_match.get("hora_fin", shift_end_time)
        validate_correction_window(editing_match["dia"], old_end, current_dt=now)

    id_torneo = match_data["id_torneo"]
    id_local = match_data["id_equipo_local"]
    id_visitante = match_data["id_equipo_visitante"]

    if id_local == id_visitante:
        raise ValueError("Los equipos local y visitante deben ser distintos.")

    local_team = teams_by_id.get(id_local)
    visit_team = teams_by_id.get(id_visitante)
    if not local_team or not visit_team:
        raise ValueError("Ambos equipos deben existir.")
    if local_team["id_torneo"] != id_torneo or visit_team["id_torneo"] != id_torneo:
        raise ValueError("Ambos equipos deben pertenecer a la misma edición.")

    if roster_counts.get(id_local, 0) < 5 or roster_counts.get(id_visitante, 0) < 5:
        raise ValueError("Ambos equipos deben tener al menos 5 jugadores inscriptos.")

    dia_partido = parse_date_value(match_data["dia"])
    f_ini = parse_date_value(tournament["fecha_inicio"])
    f_fin = parse_date_value(tournament["fecha_fin"])
    if not (f_ini <= dia_partido <= f_fin):
        raise ValueError(
            f"El día del partido debe estar dentro del rango de la edición ({f_ini} a {f_fin})."
        )

    exclude_id = editing_match["id_partido"] if editing_match else None
    target_pair = tuple(sorted((id_local, id_visitante)))
    target_slot = (
        str(match_data["dia"]),
        int(match_data["id_turno"]),
        match_data["nombre_cancha"],
        int(match_data["id_complejo"]),
    )

    if match_data["estado"] != "cancelado":
        for m in existing_matches:
            if exclude_id is not None and m["id_partido"] == exclude_id:
                continue
            if m["estado"] == "cancelado":
                continue

            if m["id_torneo"] == id_torneo:
                pair = tuple(sorted((m["id_equipo_local"], m["id_equipo_visitante"])))
                if pair == target_pair:
                    raise ValueError(
                        "Ya existe un enfrentamiento entre estos equipos en la edición (salvo cancelados)."
                    )

                if int(m["numero_fecha"]) == int(match_data["numero_fecha"]):
                    if id_local in pair or id_visitante in pair:
                        raise ValueError(
                            "Un equipo no puede jugar dos veces en la misma fecha del torneo."
                        )

            slot = (
                str(m["dia"]),
                int(m["id_turno"]),
                m["nombre_cancha"],
                int(m["id_complejo"]),
            )
            if slot == target_slot:
                raise ValueError(
                    "Superposición detectada: la cancha ya está reservada en ese día y turno."
                )

    if match_data["estado"] == "jugado":
        if not can_mark_match_played(match_data["dia"], shift_end_time, current_dt=now):
            raise ValueError(
                "Solo se puede marcar un partido como jugado después de finalizar su turno."
            )

    return True
=======
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
>>>>>>> main
