CREATE DATABASE IF NOT EXISTS torneo_ucu CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;
USE torneo_ucu;
CREATE TABLE login (
 correo VARCHAR(254) PRIMARY KEY, contrasena VARCHAR(255) NOT NULL,
 rol ENUM('administrador','planillero') NOT NULL
) ENGINE=InnoDB;
CREATE TABLE facultad (id_facultad INT PRIMARY KEY AUTO_INCREMENT,nombre VARCHAR(100) NOT NULL UNIQUE);
CREATE TABLE jugador (
 ci VARCHAR(12) PRIMARY KEY, nombre VARCHAR(80) NOT NULL, apellido VARCHAR(80) NOT NULL,
 email VARCHAR(254) NOT NULL UNIQUE, fecha_nacimiento DATE NOT NULL,
 id_facultad INT NOT NULL, tipo ENUM('grado','posgrado','docente','funcionario') NOT NULL,
 FOREIGN KEY(id_facultad) REFERENCES facultad(id_facultad),
 CHECK(ci REGEXP '^[0-9]{6,12}$'), CHECK(CHAR_LENGTH(TRIM(nombre))>0),
 CHECK(CHAR_LENGTH(TRIM(apellido))>0), CHECK(email REGEXP '^[^ @]+@[^ @]+[.][^ @]+$')
);
CREATE TABLE torneo (
 id_torneo INT PRIMARY KEY AUTO_INCREMENT,nombre VARCHAR(120) NOT NULL,anio SMALLINT NOT NULL,
 semestre TINYINT NOT NULL,fecha_inicio DATE NOT NULL,fecha_fin DATE NOT NULL,
 estado ENUM('inscripción','en curso','finalizado') NOT NULL DEFAULT 'inscripción',
 UNIQUE(anio,semestre),CHECK(semestre IN (1,2)),CHECK(fecha_fin>=fecha_inicio)
);
CREATE TABLE equipo (
 id_equipo INT PRIMARY KEY AUTO_INCREMENT,nombre VARCHAR(100) NOT NULL,id_torneo INT NOT NULL,
 id_facultad INT NOT NULL,ci_capitan VARCHAR(12) NULL,
 UNIQUE(id_equipo,id_torneo),UNIQUE(id_torneo,nombre),
 FOREIGN KEY(id_torneo) REFERENCES torneo(id_torneo),
 FOREIGN KEY(id_facultad) REFERENCES facultad(id_facultad),
 FOREIGN KEY(ci_capitan) REFERENCES jugador(ci)
);
CREATE TABLE equipo_jugador_torneo (
 id_equipo INT NOT NULL,ci_jugador VARCHAR(12) NOT NULL,id_torneo INT NOT NULL,numero_camiseta TINYINT NOT NULL,
 PRIMARY KEY(id_equipo,ci_jugador,id_torneo),UNIQUE(ci_jugador,id_torneo),
 UNIQUE(id_equipo,id_torneo,numero_camiseta),
 FOREIGN KEY(id_equipo,id_torneo) REFERENCES equipo(id_equipo,id_torneo),
 FOREIGN KEY(ci_jugador) REFERENCES jugador(ci),CHECK(numero_camiseta BETWEEN 1 AND 99)
);
CREATE TABLE complejo (
 id_complejo INT PRIMARY KEY AUTO_INCREMENT,nombre VARCHAR(100) NOT NULL,
 direccion VARCHAR(200) NOT NULL,departamento VARCHAR(80) NOT NULL
);
CREATE TABLE cancha (
 nombre_cancha VARCHAR(80) NOT NULL,id_complejo INT NOT NULL,
 superficie ENUM('sintético','parquet') NOT NULL,techada BOOLEAN NOT NULL,
 PRIMARY KEY(nombre_cancha,id_complejo),FOREIGN KEY(id_complejo) REFERENCES complejo(id_complejo),CHECK(techada IN (0,1))
);
CREATE TABLE turno (
 id_turno INT PRIMARY KEY,hora_inicio TIME NOT NULL UNIQUE,hora_fin TIME NOT NULL,
 CHECK(hora_inicio IN ('18:00:00','19:00:00','20:00:00','21:00:00','22:00:00')),
 CHECK(TIMEDIFF(hora_fin,hora_inicio)='01:00:00'),CHECK(hora_fin<='23:00:00')
);
CREATE TABLE partido (
 id_partido INT PRIMARY KEY AUTO_INCREMENT,id_torneo INT NOT NULL,numero_fecha INT NOT NULL,
 id_equipo_local INT NOT NULL,id_equipo_visitante INT NOT NULL,dia DATE NOT NULL,id_turno INT NOT NULL,
 nombre_cancha VARCHAR(80) NOT NULL,id_complejo INT NOT NULL,
 estado ENUM('programado','jugado','postergado','cancelado') NOT NULL DEFAULT 'programado',
 FOREIGN KEY(id_equipo_local,id_torneo) REFERENCES equipo(id_equipo,id_torneo),
 FOREIGN KEY(id_equipo_visitante,id_torneo) REFERENCES equipo(id_equipo,id_torneo),
 FOREIGN KEY(id_turno) REFERENCES turno(id_turno),
 FOREIGN KEY(nombre_cancha,id_complejo) REFERENCES cancha(nombre_cancha,id_complejo),
 CHECK(id_equipo_local<>id_equipo_visitante),CHECK(numero_fecha>0),
 INDEX(id_torneo,numero_fecha),INDEX(dia,id_turno,nombre_cancha,id_complejo)
);
CREATE TABLE planilla_partido (
 id_partido INT NOT NULL,ci_jugador VARCHAR(12) NOT NULL,id_equipo INT NOT NULL,
 PRIMARY KEY(id_partido,ci_jugador,id_equipo),UNIQUE(id_partido,ci_jugador),
 FOREIGN KEY(id_partido) REFERENCES partido(id_partido),FOREIGN KEY(ci_jugador) REFERENCES jugador(ci),
 FOREIGN KEY(id_equipo) REFERENCES equipo(id_equipo)
);
CREATE TABLE gol (
 id_gol INT PRIMARY KEY AUTO_INCREMENT,id_partido INT NOT NULL,ci_jugador VARCHAR(12) NOT NULL,
 minuto SMALLINT NOT NULL,autogol BOOLEAN NOT NULL DEFAULT FALSE,
 FOREIGN KEY(id_partido,ci_jugador) REFERENCES planilla_partido(id_partido,ci_jugador),
 CHECK(minuto BETWEEN 0 AND 60),CHECK(autogol IN (0,1))
);
CREATE TABLE tarjeta (
 id_tarjeta INT PRIMARY KEY AUTO_INCREMENT,id_partido INT NOT NULL,ci_jugador VARCHAR(12) NOT NULL,
 minuto SMALLINT NOT NULL,color ENUM('amarilla','roja') NOT NULL,
 FOREIGN KEY(id_partido,ci_jugador) REFERENCES planilla_partido(id_partido,ci_jugador),CHECK(minuto BETWEEN 0 AND 60)
);
CREATE TABLE sancion_jugador (
 id_sancion INT PRIMARY KEY AUTO_INCREMENT,ci_jugador VARCHAR(12) NOT NULL,id_torneo INT NOT NULL,
 motivo ENUM('roja','acumulación de amarillas','disciplinaria') NOT NULL,
 numero_fecha_inicio INT NOT NULL,cantidad_fechas INT NOT NULL,
 FOREIGN KEY(ci_jugador,id_torneo) REFERENCES equipo_jugador_torneo(ci_jugador,id_torneo),
 CHECK(numero_fecha_inicio>0),CHECK(cantidad_fechas>0)
);
-- El avance protege la identidad y facultad de jugadores ya inscriptos.
DELIMITER $$
CREATE TRIGGER jugador_validar_insert BEFORE INSERT ON jugador FOR EACH ROW
BEGIN
 IF NEW.fecha_nacimiento>CURRENT_DATE() THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='La fecha de nacimiento no puede ser futura'; END IF;
END$$
CREATE TRIGGER jugador_validar_update BEFORE UPDATE ON jugador FOR EACH ROW
BEGIN
 IF NEW.fecha_nacimiento>CURRENT_DATE() THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='La fecha de nacimiento no puede ser futura'; END IF;
 IF EXISTS(SELECT 1 FROM equipo_jugador_torneo WHERE ci_jugador=OLD.ci)
 AND (NEW.ci<>OLD.ci OR NEW.id_facultad<>OLD.id_facultad OR NEW.tipo<>OLD.tipo) THEN
 SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='No se cambia CI, facultad o tipo de un jugador inscripto en este avance'; END IF;
END$$
CREATE TRIGGER partido_no_borrar_jugado BEFORE DELETE ON partido FOR EACH ROW
BEGIN
 IF OLD.estado='jugado' THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='No se elimina un partido jugado'; END IF;
END$$
DELIMITER ;
