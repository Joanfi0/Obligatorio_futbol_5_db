import threading
import unittest
from datetime import datetime
from app.domain import (
    SagaCoordinator,
    validate_tournament,
    validate_tournament_transition,
    validate_match_rules,
    can_mark_match_played,
    is_within_correction_window,
    validate_correction_window,
)
from app.web import hash_password, check_password


class Persona2DomainAndConcurrencyTests(unittest.TestCase):
    def setUp(self):
        self.tournament = {
            "id_torneo": 1,
            "nombre": "Apertura 2026",
            "estado": "en curso",
            "fecha_inicio": "2026-09-01",
            "fecha_fin": "2026-11-30",
        }
        self.teams = {
            1: {"id_equipo": 1, "nombre": "Ing Azul", "id_torneo": 1},
            2: {"id_equipo": 2, "nombre": "Ing Blanco", "id_torneo": 1},
            3: {"id_equipo": 3, "nombre": "Salud Verde", "id_torneo": 1},
            4: {"id_equipo": 4, "nombre": "Derecho Rojo", "id_torneo": 1},
            99: {"id_equipo": 99, "nombre": "Otro Torneo", "id_torneo": 2},
        }
        self.rosters = {1: 6, 2: 5, 3: 6, 4: 5, 99: 6}
        self.base_match = {
            "id_torneo": 1,
            "numero_fecha": 1,
            "id_equipo_local": 1,
            "id_equipo_visitante": 2,
            "dia": "2026-09-10",
            "id_turno": 1,
            "nombre_cancha": "Cancha A",
            "id_complejo": 1,
            "estado": "programado",
        }

    def test_password_pbkdf2_roundtrip(self):
        hashed = hash_password("ClaveSeguraUCU2026!")
        self.assertTrue(hashed.startswith("pbkdf2:sha256:600000$"))
        self.assertTrue(check_password(hashed, "ClaveSeguraUCU2026!"))
        self.assertFalse(check_password(hashed, "OtraClave"))

    def test_tournament_states_validation(self):
        vals = validate_tournament(
            {
                "nombre": "Clausura",
                "anio": "2026",
                "semestre": "2",
                "fecha_inicio": "2026-08-01",
                "fecha_fin": "2026-11-30",
            }
        )
        self.assertEqual(vals[5], "inscripcion")

        # No pasa a 'en curso' si un equipo tiene menos de 5 jugadores
        with self.assertRaises(ValueError):
            validate_tournament_transition(
                "inscripcion",
                "en curso",
                team_counts=[
                    {"nombre": "Eq 1", "jugadores": 5},
                    {"nombre": "Eq 2", "jugadores": 4},
                ],
            )

        # Pasa a 'en curso' cuando todos tienen >= 5 jugadores
        self.assertTrue(
            validate_tournament_transition(
                "inscripcion",
                "en curso",
                team_counts=[
                    {"nombre": "Eq 1", "jugadores": 5},
                    {"nombre": "Eq 2", "jugadores": 6},
                ],
            )
        )

        # No pasa a 'finalizado' si quedan partidos pendientes
        with self.assertRaises(ValueError):
            validate_tournament_transition(
                "en curso", "finalizado", pending_matches=1
            )

        self.assertTrue(
            validate_tournament_transition(
                "en curso", "finalizado", pending_matches=0
            )
        )

    def test_teams_distinct_same_edition_and_minimum_5_players(self):
        # Mismo equipo local y visitante
        with self.assertRaises(ValueError):
            validate_match_rules(
                {**self.base_match, "id_equipo_visitante": 1},
                self.tournament,
                self.teams,
                self.rosters,
                [],
                "19:00:00",
            )

        # Equipo de otra edición
        with self.assertRaises(ValueError):
            validate_match_rules(
                {**self.base_match, "id_equipo_visitante": 99},
                self.tournament,
                self.teams,
                self.rosters,
                [],
                "19:00:00",
            )

        # Equipo con menos de 5 jugadores
        with self.assertRaises(ValueError):
            validate_match_rules(
                self.base_match,
                self.tournament,
                self.teams,
                {**self.rosters, 2: 4},
                [],
                "19:00:00",
            )

    def test_repeated_matchup_blocked_unless_canceled(self):
        existing = [
            {
                "id_partido": 10,
                **self.base_match,
                "id_equipo_local": 2,
                "id_equipo_visitante": 1,
                "numero_fecha": 1,
                "dia": "2026-09-10",
                "id_turno": 1,
                "estado": "jugado",
            }
        ]
        # Mismo cruce (1 vs 2) en otra fecha y horario -> Rechazado
        candidate = {
            **self.base_match,
            "numero_fecha": 2,
            "dia": "2026-09-17",
            "id_turno": 2,
        }
        with self.assertRaises(ValueError):
            validate_match_rules(
                candidate,
                self.tournament,
                self.teams,
                self.rosters,
                existing,
                "20:00:00",
            )

        # Si el partido previo fue cancelado -> Permitido
        existing[0]["estado"] = "cancelado"
        self.assertTrue(
            validate_match_rules(
                candidate,
                self.tournament,
                self.teams,
                self.rosters,
                existing,
                "20:00:00",
            )
        )

    def test_team_cannot_play_twice_in_same_round_or_overlap_slot(self):
        existing = [
            {
                "id_partido": 10,
                **self.base_match,
            }
        ]
        # Equipo 1 intenta jugar otro partido en la misma fecha 1
        same_round = {
            **self.base_match,
            "id_equipo_local": 1,
            "id_equipo_visitante": 3,
            "dia": "2026-09-11",
            "id_turno": 2,
        }
        with self.assertRaises(ValueError):
            validate_match_rules(
                same_round,
                self.tournament,
                self.teams,
                self.rosters,
                existing,
                "20:00:00",
            )

        # Equipos 3 vs 4 en distinta fecha pero misma cancha, día y turno -> Rechazado
        same_slot = {
            **self.base_match,
            "numero_fecha": 2,
            "id_equipo_local": 3,
            "id_equipo_visitante": 4,
        }
        with self.assertRaises(ValueError):
            validate_match_rules(
                same_slot,
                self.tournament,
                self.teams,
                self.rosters,
                existing,
                "19:00:00",
            )

    def test_mark_played_after_shift_and_48h_correction_window(self):
        # Turno termina 2026-09-10 19:00:00
        before_end = datetime(2026, 9, 10, 18, 59)
        after_end = datetime(2026, 9, 10, 19, 0)
        within_48h = datetime(2026, 9, 12, 18, 59)
        after_48h = datetime(2026, 9, 12, 19, 1)

        self.assertFalse(can_mark_match_played("2026-09-10", "19:00:00", before_end))
        self.assertTrue(can_mark_match_played("2026-09-10", "19:00:00", after_end))

        self.assertTrue(is_within_correction_window("2026-09-10", "19:00:00", within_48h))
        self.assertFalse(is_within_correction_window("2026-09-10", "19:00:00", after_48h))

        with self.assertRaises(ValueError):
            validate_correction_window("2026-09-10", "19:00:00", after_48h)

    def test_saga_compensation_on_failure(self):
        state = []
        saga = SagaCoordinator()
        saga.add_step(
            "reservar_cancha",
            lambda: state.append("cancha_reservada"),
            lambda: state.append("cancha_liberada"),
        )
        saga.add_step(
            "fallo_validacion",
            lambda: (_ for _ in ()).throw(ValueError("Conflicto detectado")),
        )
        with self.assertRaises(ValueError):
            saga.execute()
        self.assertEqual(state, ["cancha_reservada", "cancha_liberada"])

    def test_concurrent_reservation_same_slot_only_one_succeeds(self):
        """Prueba intentos simultáneos de reservar la misma cancha, día y turno."""
        shared_matches = []
        db_row_lock = threading.Lock()
        barrier = threading.Barrier(2)
        results = []

        match_a = {
            **self.base_match,
            "numero_fecha": 1,
            "id_equipo_local": 1,
            "id_equipo_visitante": 2,
        }
        match_b = {
            **self.base_match,
            "numero_fecha": 2,
            "id_equipo_local": 3,
            "id_equipo_visitante": 4,
        }

        def worker(candidate, worker_id):
            barrier.wait()  # Ambos hilos disparan exactamente al mismo tiempo
            try:
                with db_row_lock:  # Simula el bloqueo FOR UPDATE de la transacción
                    validate_match_rules(
                        candidate,
                        self.tournament,
                        self.teams,
                        self.rosters,
                        shared_matches,
                        "19:00:00",
                    )
                    shared_matches.append({"id_partido": worker_id, **candidate})
                results.append(("ok", worker_id))
            except ValueError as exc:
                results.append(("error", str(exc)))

        t1 = threading.Thread(target=worker, args=(match_a, 1))
        t2 = threading.Thread(target=worker, args=(match_b, 2))
        t1.start()
        t2.start()
        t1.join()
        t2.join()

        oks = [r for r in results if r[0] == "ok"]
        errors = [r for r in results if r[0] == "error"]
        self.assertEqual(len(oks), 1)
        self.assertEqual(len(errors), 1)
        self.assertEqual(len(shared_matches), 1)


if __name__ == "__main__":
    unittest.main()