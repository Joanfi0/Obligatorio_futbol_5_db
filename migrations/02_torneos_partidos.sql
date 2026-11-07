USE torneo_ucu;

GRANT INSERT, UPDATE, DELETE ON torneo_ucu.torneo TO 'torneo_admin'@'%';
GRANT INSERT, UPDATE, DELETE ON torneo_ucu.partido TO 'torneo_admin'@'%';
FLUSH PRIVILEGES;

DROP TRIGGER IF EXISTS partido_validar_insert;
DROP TRIGGER IF EXISTS partido_validar_update;

DELIMITER $$

CREATE TRIGGER partido_validar_insert BEFORE INSERT ON partido FOR EACH ROW
BEGIN
    DECLARE v_estado_torneo VARCHAR(20);
    DECLARE v_jugadores_local INT;
    DECLARE v_jugadores_visitante INT;
    DECLARE v_hora_fin TIME;

    SELECT estado INTO v_estado_torneo FROM torneo WHERE id_torneo = NEW.id_torneo;
    IF v_estado_torneo = 'finalizado' THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'No se pueden programar partidos en una edicion finalizada';
    END IF;

    SELECT COUNT(*) INTO v_jugadores_local
    FROM equipo_jugador_torneo
    WHERE id_equipo = NEW.id_equipo_local AND id_torneo = NEW.id_torneo;

    SELECT COUNT(*) INTO v_jugadores_visitante
    FROM equipo_jugador_torneo
    WHERE id_equipo = NEW.id_equipo_visitante AND id_torneo = NEW.id_torneo;

    IF v_jugadores_local < 5 OR v_jugadores_visitante < 5 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Ambos equipos deben tener al menos 5 jugadores inscriptos';
    END IF;

    IF NEW.estado <> 'cancelado' THEN
        IF EXISTS (
            SELECT 1 FROM partido
            WHERE id_torneo = NEW.id_torneo
              AND estado <> 'cancelado'
              AND LEAST(id_equipo_local, id_equipo_visitante) = LEAST(NEW.id_equipo_local, NEW.id_equipo_visitante)
              AND GREATEST(id_equipo_local, id_equipo_visitante) = GREATEST(NEW.id_equipo_local, NEW.id_equipo_visitante)
        ) THEN
            SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Los equipos ya tienen un enfrentamiento activo en esta edicion';
        END IF;

        IF EXISTS (
            SELECT 1 FROM partido
            WHERE id_torneo = NEW.id_torneo
              AND numero_fecha = NEW.numero_fecha
              AND estado <> 'cancelado'
              AND (
                  id_equipo_local IN (NEW.id_equipo_local, NEW.id_equipo_visitante)
                  OR id_equipo_visitante IN (NEW.id_equipo_local, NEW.id_equipo_visitante)
              )
        ) THEN
            SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Uno de los equipos ya juega en esta fecha del torneo';
        END IF;

        IF EXISTS (
            SELECT 1 FROM partido
            WHERE dia = NEW.dia
              AND id_turno = NEW.id_turno
              AND nombre_cancha = NEW.nombre_cancha
              AND id_complejo = NEW.id_complejo
              AND estado <> 'cancelado'
        ) THEN
            SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Superposicion de cancha, dia y turno';
        END IF;
    END IF;

    IF NEW.estado = 'jugado' THEN
        SELECT hora_fin INTO v_hora_fin FROM turno WHERE id_turno = NEW.id_turno;
        IF TIMESTAMP(NEW.dia, v_hora_fin) > NOW() THEN
            SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Solo se puede marcar como jugado despues de finalizar su turno';
        END IF;
    END IF;
END$$

CREATE TRIGGER partido_validar_update BEFORE UPDATE ON partido FOR EACH ROW
BEGIN
    DECLARE v_estado_torneo VARCHAR(20);
    DECLARE v_jugadores_local INT;
    DECLARE v_jugadores_visitante INT;
    DECLARE v_hora_fin_old TIME;
    DECLARE v_hora_fin_new TIME;

    SELECT estado INTO v_estado_torneo FROM torneo WHERE id_torneo = NEW.id_torneo;
    IF v_estado_torneo = 'finalizado' THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'No se pueden modificar partidos de una edicion finalizada';
    END IF;

    IF OLD.estado = 'jugado' THEN
        SELECT hora_fin INTO v_hora_fin_old FROM turno WHERE id_turno = OLD.id_turno;
        IF TIMESTAMPADD(HOUR, 48, TIMESTAMP(OLD.dia, v_hora_fin_old)) < NOW() THEN
            SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Plazo de correccion de 48 horas vencido para este partido jugado';
        END IF;
    END IF;

    SELECT COUNT(*) INTO v_jugadores_local
    FROM equipo_jugador_torneo
    WHERE id_equipo = NEW.id_equipo_local AND id_torneo = NEW.id_torneo;

    SELECT COUNT(*) INTO v_jugadores_visitante
    FROM equipo_jugador_torneo
    WHERE id_equipo = NEW.id_equipo_visitante AND id_torneo = NEW.id_torneo;

    IF v_jugadores_local < 5 OR v_jugadores_visitante < 5 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Ambos equipos deben tener al menos 5 jugadores inscriptos';
    END IF;

    IF NEW.estado <> 'cancelado' THEN
        IF EXISTS (
            SELECT 1 FROM partido
            WHERE id_torneo = NEW.id_torneo
              AND id_partido <> OLD.id_partido
              AND estado <> 'cancelado'
              AND LEAST(id_equipo_local, id_equipo_visitante) = LEAST(NEW.id_equipo_local, NEW.id_equipo_visitante)
              AND GREATEST(id_equipo_local, id_equipo_visitante) = GREATEST(NEW.id_equipo_local, NEW.id_equipo_visitante)
        ) THEN
            SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Los equipos ya tienen un enfrentamiento activo en esta edicion';
        END IF;

        IF EXISTS (
            SELECT 1 FROM partido
            WHERE id_torneo = NEW.id_torneo
              AND id_partido <> OLD.id_partido
              AND numero_fecha = NEW.numero_fecha
              AND estado <> 'cancelado'
              AND (
                  id_equipo_local IN (NEW.id_equipo_local, NEW.id_equipo_visitante)
                  OR id_equipo_visitante IN (NEW.id_equipo_local, NEW.id_equipo_visitante)
              )
        ) THEN
            SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Uno de los equipos ya juega en esta fecha del torneo';
        END IF;

        IF EXISTS (
            SELECT 1 FROM partido
            WHERE id_partido <> OLD.id_partido
              AND dia = NEW.dia
              AND id_turno = NEW.id_turno
              AND nombre_cancha = NEW.nombre_cancha
              AND id_complejo = NEW.id_complejo
              AND estado <> 'cancelado'
        ) THEN
            SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Superposicion de cancha, dia y turno';
        END IF;
    END IF;

    IF NEW.estado = 'jugado' THEN
        SELECT hora_fin INTO v_hora_fin_new FROM turno WHERE id_turno = NEW.id_turno;
        IF TIMESTAMP(NEW.dia, v_hora_fin_new) > NOW() THEN
            SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Solo se puede marcar como jugado despues de finalizar su turno';
        END IF;
    END IF;
END$$

DELIMITER ;