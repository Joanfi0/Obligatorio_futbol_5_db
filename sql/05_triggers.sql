DELIMITER $$

CREATE TRIGGER trg_sancion_automatica
AFTER INSERT ON tarjeta
FOR EACH ROW
BEGIN
    DECLARE v_torneo INT;
    DECLARE v_fecha INT;
    DECLARE v_amarillas INT;

    -- Obtener el torneo y la fecha del partido.
    SELECT p.id_torneo, p.numero_fecha
    INTO v_torneo, v_fecha
    FROM partido p
    WHERE p.id_partido = NEW.id_partido;

    -- Una tarjeta roja genera una fecha de suspensión.
    IF NEW.color = 'roja' THEN

        INSERT INTO sancion_jugador (
            ci_jugador,
            id_torneo,
            motivo,
            numero_fecha_inicio,
            cantidad_fechas
        )
        SELECT
            NEW.ci_jugador,
            v_torneo,
            'roja',
            v_fecha + 1,
            1
        WHERE NOT EXISTS (
            SELECT 1
            FROM sancion_jugador s
            WHERE s.ci_jugador = NEW.ci_jugador
              AND s.id_torneo = v_torneo
              AND s.motivo = 'roja'
              AND s.numero_fecha_inicio = v_fecha + 1
        );

    -- Las tarjetas amarillas se acumulan durante el torneo.
    ELSEIF NEW.color = 'amarilla' THEN

        SELECT COUNT(*)
        INTO v_amarillas
        FROM tarjeta t
        JOIN partido p ON p.id_partido = t.id_partido
        WHERE t.ci_jugador = NEW.ci_jugador
          AND t.color = 'amarilla'
          AND p.id_torneo = v_torneo
          AND p.numero_fecha <= v_fecha;

        -- Cada acumulación de tres amarillas genera una sanción.
        IF MOD(v_amarillas, 3) = 0 THEN

            INSERT INTO sancion_jugador (
                ci_jugador,
                id_torneo,
                motivo,
                numero_fecha_inicio,
                cantidad_fechas
            )
            SELECT
                NEW.ci_jugador,
                v_torneo,
                'acumulacion de amarillas',
                v_fecha + 1,
                1
            WHERE NOT EXISTS (
                SELECT 1
                FROM sancion_jugador s
                WHERE s.ci_jugador = NEW.ci_jugador
                  AND s.id_torneo = v_torneo
                  AND s.motivo = 'acumulacion de amarillas'
                  AND s.numero_fecha_inicio = v_fecha + 1
            );

        END IF;

    END IF;
END$$

DELIMITER ;