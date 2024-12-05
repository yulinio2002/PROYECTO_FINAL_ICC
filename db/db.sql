create database db_icc;

use db_icc;

CREATE TABLE usuario (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    apellido VARCHAR(100) NOT NULL,
    email VARCHAR(150) NOT NULL UNIQUE,
    username VARCHAR(50) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    telefono VARCHAR(15) DEFAULT NULL, -- Campo opcional
    direccion TEXT DEFAULT NULL, -- Campo opcional
    rol ENUM('admin', 'guard', 'user') DEFAULT 'user', -- Rol por defecto
    estado ENUM('activo', 'inactivo') DEFAULT 'inactivo', -- Estado por defecto
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP, -- Automático
    ultimo_acceso TIMESTAMP NULL, -- Puede ser NULL hasta que el usuario inicie sesión
    propietario_condominio_id INT DEFAULT NULL, -- Opcional
    foto_perfil VARCHAR(255) DEFAULT NULL -- Opcional
);

INSERT INTO usuario (nombre, apellido, email, username, password, estado, rol)
VALUES ('Andres', 'Sempertegui', 'andres.semper@gmail.com', 'Rick23', '1234', 'activo', 'admin');

INSERT INTO usuario (nombre, apellido, email, username, password, estado)
VALUES ('Juan', 'Perez', 'juan.perez@example.com', 'juanp', 'password123', 'activo');


CREATE TABLE vehiculos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    placa VARCHAR(10) UNIQUE NOT NULL,             -- Placa única del vehículo
    marca VARCHAR(50),                             -- Marca del vehículo
    modelo VARCHAR(50),                            -- Modelo del vehículo
    color VARCHAR(30),                             -- Color del vehículo
    propietario VARCHAR(100),                      -- Nombre del propietario
    telefono_contacto VARCHAR(15) DEFAULT NULL,    -- Teléfono del propietario (puede ser NULL)
    email_contacto VARCHAR(100) DEFAULT NULL,      -- Correo del propietario (puede ser NULL)
    estado_ubicacion ENUM('Adentro', 'Afuera') DEFAULT 'Afuera', -- Estado del vehículo
    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP -- Fecha de registro
);

CREATE TABLE capturas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    placa_detectada VARCHAR(10),           -- Placa detectada (puede no coincidir con las registradas)
    imagen_placa VARCHAR(255) DEFAULT NULL, -- Ruta relativa de la imagen almacenada (puede ser NULL)
    fecha_captura TIMESTAMP DEFAULT CURRENT_TIMESTAMP, -- Fecha y hora de captura
    estado_identificado ENUM('SI', 'NO') DEFAULT NULL, -- Si el vehículo fue identificado
    vehiculo_id INT,                       -- Relación con el vehículo (puede ser NULL si no identificado)
    FOREIGN KEY (vehiculo_id) REFERENCES vehiculos(id)
);

CREATE TABLE eventos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    tipo_evento VARCHAR(50),                -- Tipo de evento (e.g., Entrada, Salida)
    descripcion TEXT DEFAULT NULL,          -- Detalles adicionales (puede ser NULL)
    fecha_evento TIMESTAMP DEFAULT CURRENT_TIMESTAMP, -- Fecha y hora del evento
    vehiculo_id INT,                        -- Relación con el vehículo (opcional)
    FOREIGN KEY (vehiculo_id) REFERENCES vehiculos(id)
);
