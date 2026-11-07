
-- Usuarios locales de demostracion. Cambiar aqui y en .env antes de publicar.
CREATE USER 'torneo_auth'@'%' IDENTIFIED BY 'AuthDemo_UCU_2026!';
CREATE USER 'torneo_admin'@'%' IDENTIFIED BY 'AdminDB_UCU_2026!';
CREATE USER 'torneo_plan'@'%' IDENTIFIED BY 'PlanDB_UCU_2026!';

GRANT SELECT ON torneo_ucu.login TO 'torneo_auth'@'%';

-- El administrador puede consultar y gestionar jugadores y equipos.
GRANT SELECT ON torneo_ucu.* TO 'torneo_admin'@'%';
GRANT INSERT, UPDATE, DELETE
ON torneo_ucu.jugador TO 'torneo_admin'@'%';
GRANT INSERT, UPDATE, DELETE
ON torneo_ucu.equipo TO 'torneo_admin'@'%';
GRANT INSERT, UPDATE, DELETE
ON torneo_ucu.equipo_jugador_torneo TO 'torneo_admin'@'%';
GRANT INSERT, UPDATE, DELETE
ON torneo_ucu.complejo TO 'torneo_admin'@'%';
GRANT INSERT, UPDATE, DELETE
ON torneo_ucu.cancha TO 'torneo_admin'@'%';
-- UPDATE is required for locking reads that join turno while managing matches.
GRANT UPDATE ON torneo_ucu.turno TO 'torneo_admin'@'%';
GRANT SELECT ON torneo_ucu.complejo TO 'torneo_admin'@'%';

GRANT INSERT, UPDATE, DELETE ON torneo_ucu.torneo TO 'torneo_admin'@'%';
GRANT INSERT, UPDATE, DELETE ON torneo_ucu.partido TO 'torneo_admin'@'%';

-- Planillero: solo lectura del fixture en este avance.
-- Escritura aun pendiente.
GRANT SELECT ON torneo_ucu.torneo TO 'torneo_plan'@'%';
GRANT SELECT ON torneo_ucu.partido TO 'torneo_plan'@'%';
GRANT SELECT ON torneo_ucu.equipo TO 'torneo_plan'@'%';
GRANT SELECT ON torneo_ucu.turno TO 'torneo_plan'@'%';
GRANT SELECT ON torneo_ucu.planilla_partido
TO 'torneo_plan'@'%';
GRANT SELECT ON torneo_ucu.jugador
TO 'torneo_plan'@'%';

GRANT SELECT ON torneo_ucu.equipo_jugador_torneo
TO 'torneo_plan'@'%';

GRANT SELECT ON torneo_ucu.sancion_jugador
TO 'torneo_plan'@'%';

GRANT INSERT ON torneo_ucu.planilla_partido
TO 'torneo_plan'@'%';
GRANT SELECT, INSERT ON torneo_ucu.gol
TO 'torneo_plan'@'%';

GRANT SELECT, INSERT ON torneo_ucu.tarjeta
TO 'torneo_plan'@'%';
GRANT INSERT ON torneo_ucu.sancion_jugador
TO 'torneo_admin'@'%';

GRANT SELECT ON torneo_ucu.complejo TO 'torneo_plan'@'%';
GRANT SELECT ON torneo_ucu.v_resultados TO 'torneo_plan'@'%';
GRANT INSERT,UPDATE,DELETE ON torneo_ucu.planilla_partido TO 'torneo_admin'@'%';
GRANT INSERT,UPDATE,DELETE ON torneo_ucu.gol TO 'torneo_admin'@'%';
GRANT INSERT,UPDATE,DELETE ON torneo_ucu.tarjeta TO 'torneo_admin'@'%';
GRANT UPDATE,DELETE ON torneo_ucu.planilla_partido TO 'torneo_plan'@'%';
GRANT UPDATE,DELETE ON torneo_ucu.gol TO 'torneo_plan'@'%';
GRANT UPDATE,DELETE ON torneo_ucu.tarjeta TO 'torneo_plan'@'%';
GRANT UPDATE,DELETE ON torneo_ucu.sancion_jugador TO 'torneo_admin'@'%';
GRANT SELECT ON torneo_ucu.cancha TO 'torneo_plan'@'%';


