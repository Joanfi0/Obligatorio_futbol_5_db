-- Aplicar como administrador MySQL en bases ya inicializadas.
GRANT INSERT, UPDATE, DELETE ON torneo_ucu.equipo TO 'torneo_admin'@'%';
GRANT INSERT, UPDATE, DELETE ON torneo_ucu.equipo_jugador_torneo TO 'torneo_admin'@'%';
GRANT INSERT, UPDATE, DELETE ON torneo_ucu.complejo TO 'torneo_admin'@'%';
GRANT INSERT, UPDATE, DELETE ON torneo_ucu.cancha TO 'torneo_admin'@'%';
-- UPDATE is required for locking reads that join turno while managing matches.
GRANT UPDATE ON torneo_ucu.turno TO 'torneo_admin'@'%';
