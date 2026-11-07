-- Aplicar como administrador MySQL en bases ya inicializadas.
GRANT INSERT, UPDATE, DELETE
ON torneo_ucu.cancha TO 'torneo_admin'@'%';
