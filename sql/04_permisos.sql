
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

-- Planillero: solo lectura del fixture en este avance.
-- Escritura aun pendiente.
GRANT SELECT ON torneo_ucu.torneo TO 'torneo_plan'@'%';
GRANT SELECT ON torneo_ucu.partido TO 'torneo_plan'@'%';
GRANT SELECT ON torneo_ucu.equipo TO 'torneo_plan'@'%';
GRANT SELECT ON torneo_ucu.turno TO 'torneo_plan'@'%';
