-- EcoSmart UCO - Estructura de referencia de la base de datos (MariaDB / MySQL)
-- Coincide con el INSERT del flujo de Node-RED (servidor/nodered/flujo_ecosmart.json).
-- Si el servidor ya existe, compárela con:  SHOW CREATE TABLE iot.valores;

CREATE DATABASE IF NOT EXISTS iot CHARACTER SET utf8mb4;
USE iot;

CREATE TABLE IF NOT EXISTS valores (
  id          INT AUTO_INCREMENT PRIMARY KEY,
  nodo_id     VARCHAR(20)  NOT NULL,   -- JSON: nodo_Id      (ej. ECO-2)
  estado      VARCHAR(20)  NOT NULL,   -- JSON: estado       (DISPONIBLE, MEDIO, LLENO, LLENO _UMBRAL)
  mensaje_id  INT          NOT NULL,   -- JSON: msg_id       (contador del nodo)
  distancia   DECIMAL(6,1) NOT NULL,   -- JSON: distancia_cm
  fecha       DATETIME     NOT NULL,   -- NOW() del servidor (zona -05:00)
  INDEX idx_nodo_fecha (nodo_id, fecha)
);

-- Usuarios con permisos mínimos (cambiar las contraseñas)
CREATE USER IF NOT EXISTS 'nodered'@'localhost' IDENTIFIED BY 'CAMBIAR_CLAVE_1';
GRANT INSERT, SELECT ON iot.* TO 'nodered'@'localhost';
CREATE USER IF NOT EXISTS 'grafana'@'localhost' IDENTIFIED BY 'CAMBIAR_CLAVE_2';
GRANT SELECT ON iot.* TO 'grafana'@'localhost';
FLUSH PRIVILEGES;
