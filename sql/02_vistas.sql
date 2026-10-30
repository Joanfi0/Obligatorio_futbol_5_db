USE torneo_ucu;
CREATE VIEW v_resultados AS
SELECT p.id_partido,p.id_torneo,p.numero_fecha,p.id_equipo_local,p.id_equipo_visitante,
 SUM(CASE WHEN (pp.id_equipo=p.id_equipo_local AND g.autogol=0) OR (pp.id_equipo=p.id_equipo_visitante AND g.autogol=1) THEN 1 ELSE 0 END) goles_local,
 SUM(CASE WHEN (pp.id_equipo=p.id_equipo_visitante AND g.autogol=0) OR (pp.id_equipo=p.id_equipo_local AND g.autogol=1) THEN 1 ELSE 0 END) goles_visitante
FROM partido p LEFT JOIN gol g ON g.id_partido=p.id_partido
LEFT JOIN planilla_partido pp ON pp.id_partido=g.id_partido AND pp.ci_jugador=g.ci_jugador
WHERE p.estado='jugado'
GROUP BY p.id_partido,p.id_torneo,p.numero_fecha,p.id_equipo_local,p.id_equipo_visitante;
CREATE VIEW v_actuaciones AS
SELECT id_torneo,id_partido,id_equipo_local id_equipo,goles_local gf,goles_visitante gc FROM v_resultados
UNION ALL
SELECT id_torneo,id_partido,id_equipo_visitante,goles_visitante,goles_local FROM v_resultados;
CREATE VIEW v_posiciones AS
SELECT e.id_torneo,e.id_equipo,e.nombre,COUNT(a.id_partido) jugados,
 COALESCE(SUM(a.gf>a.gc),0) ganados,COALESCE(SUM(a.gf=a.gc),0) empatados,
 COALESCE(SUM(a.gf<a.gc),0) perdidos,COALESCE(SUM(a.gf),0) goles_favor,
 COALESCE(SUM(a.gc),0) goles_contra,COALESCE(SUM(a.gf-a.gc),0) diferencia,
 COALESCE(SUM(CASE WHEN a.gf>a.gc THEN 3 WHEN a.gf=a.gc THEN 1 ELSE 0 END),0) puntos
FROM equipo e LEFT JOIN v_actuaciones a ON a.id_equipo=e.id_equipo AND a.id_torneo=e.id_torneo
GROUP BY e.id_torneo,e.id_equipo,e.nombre;
