"""Pruebas portables del dominio y datos. SQLite solo es un oráculo de prueba,
NO es la base de la aplicación ni reemplaza la validación pendiente en MySQL."""
import ast
import json
from pathlib import Path
import re
import sqlite3
import unittest
from datetime import date
from app.domain import validate_player

ROOT=Path(__file__).resolve().parents[1]
COLS={
'login':'correo contrasena rol',
'facultad':'id_facultad nombre',
'jugador':'ci nombre apellido email fecha_nacimiento id_facultad tipo',
'torneo':'id_torneo nombre anio semestre fecha_inicio fecha_fin estado',
'equipo':'id_equipo nombre id_torneo id_facultad ci_capitan',
'equipo_jugador_torneo':'id_equipo ci_jugador id_torneo numero_camiseta',
'complejo':'id_complejo nombre direccion departamento',
'cancha':'nombre_cancha id_complejo superficie techada',
'turno':'id_turno hora_inicio hora_fin',
'partido':'id_partido id_torneo numero_fecha id_equipo_local id_equipo_visitante dia id_turno nombre_cancha id_complejo estado',
'planilla_partido':'id_partido ci_jugador id_equipo',
'gol':'id_gol id_partido ci_jugador minuto autogol',
'tarjeta':'id_tarjeta id_partido ci_jugador minuto color',
'sancion_jugador':'id_sancion ci_jugador id_torneo motivo numero_fecha_inicio cantidad_fechas'}

def data():
    out={k:[] for k in COLS}
    for line in (ROOT/'sql/03_datos.sql').read_text(encoding='utf-8').splitlines():
        m=re.match(r'INSERT INTO (\w+) VALUES (.*);$',line)
        if m:
            row=ast.literal_eval(m[2].replace('NULL','None'))
            out[m[1]].append(dict(zip(COLS[m[1]].split(),row)))
    return out

class DomainTests(unittest.TestCase):
    def setUp(self):
        self.valid=dict(ci='59999999',nombre='Prueba',apellido='Local',email='p@example.test',fecha_nacimiento='2000-01-01',id_facultad='1',tipo='grado')
    def test_valid_player(self):self.assertEqual(validate_player(self.valid)[0],'59999999')
    def test_invalid_values(self):
        for k,v in [('ci','abc'),('nombre',' '),('email','sin-correo'),('fecha_nacimiento','2999-01-01'),('tipo','visitante'),('id_facultad','0')]:
            with self.subTest(k=k):
                with self.assertRaises(ValueError):validate_player({**self.valid,k:v})

class FixtureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.d=data()
    def test_six_teams_three_played_rounds(self):
        self.assertEqual(len(self.d['equipo']),6)
        played=[p for p in self.d['partido'] if p['estado']=='jugado']
        self.assertEqual(len(played),9)
        self.assertEqual({p['numero_fecha'] for p in played},{1,2,3})
    def test_rosters_and_captains(self):
        players={p['ci']:p for p in self.d['jugador']};seen=set()
        for e in self.d['equipo']:
            roster=[r for r in self.d['equipo_jugador_torneo'] if r['id_equipo']==e['id_equipo']]
            self.assertTrue(5<=len(roster)<=10)
            self.assertIn(e['ci_capitan'],[r['ci_jugador'] for r in roster])
            self.assertLessEqual(sum(players[r['ci_jugador']]['tipo'] in ('docente','funcionario') for r in roster),2)
            for r in roster:
                self.assertEqual(players[r['ci_jugador']]['id_facultad'],e['id_facultad'])
                identity=(r['ci_jugador'],r['id_torneo']);self.assertNotIn(identity,seen);seen.add(identity)
    def test_schedule_and_dates(self):
        pairs=set();team_rounds=set();slots=set()
        for p in self.d['partido']:
            date.fromisoformat(p['dia'])
            if p['estado']=='cancelado':continue
            pair=(p['id_torneo'],*sorted([p['id_equipo_local'],p['id_equipo_visitante']]))
            self.assertNotIn(pair,pairs);pairs.add(pair)
            for team in (p['id_equipo_local'],p['id_equipo_visitante']):
                key=(p['id_torneo'],p['numero_fecha'],team);self.assertNotIn(key,team_rounds);team_rounds.add(key)
            slot=(p['dia'],p['id_turno'],p['nombre_cancha'],p['id_complejo']);self.assertNotIn(slot,slots);slots.add(slot)
    def test_sheet_membership_and_suspensions(self):
        matches={p['id_partido']:p for p in self.d['partido']}
        membership={(r['ci_jugador'],r['id_equipo'],r['id_torneo']) for r in self.d['equipo_jugador_torneo']}
        for row in self.d['planilla_partido']:
            p=matches[row['id_partido']]
            self.assertIn(row['id_equipo'],(p['id_equipo_local'],p['id_equipo_visitante']))
            self.assertIn((row['ci_jugador'],row['id_equipo'],p['id_torneo']),membership)
            for s in self.d['sancion_jugador']:
                if s['ci_jugador']==row['ci_jugador'] and s['id_torneo']==p['id_torneo']:
                    self.assertFalse(s['numero_fecha_inicio']<=p['numero_fecha']<s['numero_fecha_inicio']+s['cantidad_fechas'])
        present={(p['id_partido'],p['ci_jugador']) for p in self.d['planilla_partido']}
        for row in self.d['gol']+self.d['tarjeta']:self.assertIn((row['id_partido'],row['ci_jugador']),present)

class ReportOracleTests(unittest.TestCase):
    def setUp(self):
        self.db=sqlite3.connect(':memory:');self.db.row_factory=sqlite3.Row
        self.db.create_function('IF',3,lambda c,a,b:a if c else b)
        for name,cols in COLS.items():self.db.execute('CREATE TABLE '+name+' ('+','.join(cols.split())+')')
        self.d=data()
        for table,rows in self.d.items():
            for row in rows:self.db.execute('INSERT INTO '+table+' VALUES ('+','.join('?' for _ in row)+')',tuple(row.values()))
        self.db.executescript((ROOT/'sql/02_vistas.sql').read_text(encoding='utf-8').replace('USE torneo_ucu;',''))
    def tearDown(self):self.db.close()
    def test_standings_balance(self):
        rows=self.db.execute('SELECT * FROM v_posiciones').fetchall()
        self.assertEqual(sum(r['jugados'] for r in rows),18)
        self.assertEqual(sum(r['goles_favor'] for r in rows),len(self.d['gol']))
        self.assertEqual(sum(r['goles_favor'] for r in rows),sum(r['goles_contra'] for r in rows))
        for r in rows:self.assertEqual(r['puntos'],3*r['ganados']+r['empatados'])
    def test_own_goal_counts_for_opponent(self):
        r=self.db.execute('SELECT * FROM v_resultados WHERE id_partido=1').fetchone()
        self.assertEqual((r['goles_local'],r['goles_visitante']),(3,1))
    def test_report_queries_portable_subset(self):
        reports=json.loads((ROOT/'app/reports.json').read_text(encoding='utf-8'))
        for key,(_,sql) in reports.items():
            if key=='promedios':continue # GROUPING/WITH ROLLUP son específicos del motor objetivo.
            with self.subTest(key=key):self.assertTrue(self.db.execute(sql.replace('%s','?'),(1,)).fetchall())
        missing=reports['sinparticipar'][1]
        self.assertEqual(len(self.db.execute(missing.replace('%s','?'),(1,)).fetchall()),6)

if __name__=='__main__':unittest.main()
