CREATE DATABASE IF NOT EXISTS BD_Tienda;

USE BD_Tienda;

-- 1. PROVEEDOR
CREATE TABLE PROVEEDOR (
    idProveedor INT AUTO_INCREMENT NOT NULL,
    nombre VARCHAR(20) NOT NULL UNIQUE,
    telefono VARCHAR(15) NULL UNIQUE,
    correo VARCHAR(30) NULL,
    estado BIT,
    nit VARCHAR(10) NULL,
    direccion VARCHAR(50) NULL,
    CONSTRAINT pk_proveedor PRIMARY KEY (idProveedor)
);

-- 2. PRODUCTO (Agregado UNSIGNED y CHECK en precios)
CREATE TABLE PRODUCTO (
    idProducto INT AUTO_INCREMENT NOT NULL,
    nombre VARCHAR(20) NOT NULL,
    referencia VARCHAR(20) NOT NULL,
    precio_compra DECIMAL(10, 2) NOT NULL CHECK (precio_compra >= 0),
    precio_venta DECIMAL(10, 2) NOT NULL CHECK (precio_venta >= 0),
    bodega INT UNSIGNED DEFAULT 0, -- UNSIGNED impide negativos
    descripcion VARCHAR(128) NOT NULL,
    CONSTRAINT pk_producto PRIMARY KEY (idProducto)
);

-- 3. CUENTA_EMPRESA
CREATE TABLE CUENTA_EMPRESA (
    idCuenta_empresa INT AUTO_INCREMENT NOT NULL,
    idProveedor INT,
    referencia VARCHAR(20) NOT NULL,
    precio_compra DECIMAL(10, 2) NOT NULL CHECK (precio_compra >= 0),
    precio_venta DECIMAL(10, 2) NOT NULL CHECK (precio_venta >= 0),
    bodega INT UNSIGNED DEFAULT 0,
    descripcion VARCHAR(128) NOT NULL,
    CONSTRAINT pk_cuenta_empresa PRIMARY KEY (idCuenta_empresa),
    FOREIGN KEY (idProveedor) REFERENCES PROVEEDOR (idProveedor)
);

-- 4. EMPLEADO
CREATE TABLE EMPLEADO (
    idEmpleado INT AUTO_INCREMENT NOT NULL,
    nombre VARCHAR(20) NOT NULL,
    documento VARCHAR(20) NULL,
    trabajo_hora DECIMAL(10, 2) NOT NULL CHECK (trabajo_hora >= 0),
    pago_hora DECIMAL(10, 2) NOT NULL CHECK (pago_hora >= 0),
    telefono VARCHAR(15) NULL,
    correo VARCHAR(30) NULL,
    CONSTRAINT pk_empleado PRIMARY KEY (idEmpleado)
);

-- 5. COMPRA
CREATE TABLE COMPRA (
    idCompra INT AUTO_INCREMENT NOT NULL,
    idEmpleado INT,
    idProveedor INT,
    fechacompra TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT pk_compra PRIMARY KEY (idCompra),
    FOREIGN KEY (idEmpleado) REFERENCES EMPLEADO (idEmpleado),
    FOREIGN KEY (idProveedor) REFERENCES PROVEEDOR (idProveedor)
);

-- 6. DETALLE_COMPRA (Cantidad protegida)
CREATE TABLE DETALLE_COMPRA (
    idDetalle_compra INT AUTO_INCREMENT NOT NULL,
    idProducto INT,
    idCompra INT,
    cantidad INT UNSIGNED NOT NULL CHECK (cantidad > 0), -- Debe ser al menos 1
    CONSTRAINT pk_detalle_compra PRIMARY KEY (idDetalle_compra),
    FOREIGN KEY (idProducto) REFERENCES PRODUCTO (idProducto),
    FOREIGN KEY (idCompra) REFERENCES COMPRA (idCompra)
);

-- 7. CLIENTE
CREATE TABLE CLIENTE (
    idCliente INT AUTO_INCREMENT NOT NULL,
    nombre VARCHAR(20) NOT NULL,
    apellidos VARCHAR(50) NOT NULL,
    documento VARCHAR(11) NOT NULL UNIQUE,
    telefono VARCHAR(15) NULL,
    correo VARCHAR(30) NULL,
    direccion VARCHAR(50) NULL,
    CONSTRAINT pk_cliente PRIMARY KEY (idCliente)
);

-- 8. METODO_DE_PAGO
CREATE TABLE METODO_DE_PAGO (
    idMetodo_de_pago INT AUTO_INCREMENT NOT NULL,
    nombre VARCHAR(20) NOT NULL,
    num_cuenta VARCHAR(16) NOT NULL UNIQUE,
    CONSTRAINT pk_metodo_pago PRIMARY KEY (idMetodo_de_pago)
);

-- 9. VENTA (Valor total protegido)
CREATE TABLE VENTA (
    idVenta INT AUTO_INCREMENT NOT NULL,
    idEmpleado INT,
    fecha_venta TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    estado_pago VARCHAR(10) NOT NULL,
    valor_total DECIMAL(10, 2) NOT NULL CHECK (valor_total >= 0),
    CONSTRAINT pk_venta PRIMARY KEY (idVenta),
    FOREIGN KEY (idEmpleado) REFERENCES EMPLEADO (idEmpleado)
);

-- 10. PAGO
CREATE TABLE PAGO (
    idPago INT AUTO_INCREMENT NOT NULL,
    idCliente INT,
    idVenta INT,
    idMetodo_de_pago INT,
    monto DECIMAL(10, 2) NOT NULL CHECK (monto >= 0),
    fecha_pago TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT pk_pago PRIMARY KEY (idPago),
    FOREIGN KEY (idCliente) REFERENCES CLIENTE (idCliente),
    FOREIGN KEY (idVenta) REFERENCES VENTA (idVenta),
    FOREIGN KEY (idMetodo_de_pago) REFERENCES METODO_DE_PAGO (idMetodo_de_pago)
);

-- 11. DETALLE_VENTA (Cantidad protegida)
CREATE TABLE DETALLE_VENTA (
    idDetalle_venta INT AUTO_INCREMENT NOT NULL,
    idProducto INT,
    idVenta INT,
    cantidad INT UNSIGNED NOT NULL CHECK (cantidad > 0),
    CONSTRAINT pk_detalle_venta PRIMARY KEY (idDetalle_venta),
    FOREIGN KEY (idProducto) REFERENCES PRODUCTO (idProducto),
    FOREIGN KEY (idVenta) REFERENCES VENTA (idVenta)
);

--12. ENVIO 
CREATE TABLE ENVIO (
    idEnvio INT AUTO_INCREMENT NOT NULL,
    idCompra INT NOT NULL,
    idEmpleado INT NOT NULL,
    fecha DATE,
    valor DECIMAL(10,2),
    CONSTRAINT pk_envio PRIMARY KEY (idEnvio),
    CONSTRAINT fk_idEmpleado FOREIGN KEY (idEmpleado) REFERENCES EMPLEADO (idEmpleado),
    CONSTRAINT fk_idCompra FOREIGN KEY (idCompra) REFERENCES COMPRA (idCompra)
);

alter table empleado add column rol bit(1) NOT NULL DEFAULT 0;

-- 13. PAGO_EMPLEADO (registro de pagos de nómina al empleado)
CREATE TABLE IF NOT EXISTS PAGO_EMPLEADO (
    idPago_empleado INT AUTO_INCREMENT NOT NULL,
    idEmpleado      INT NOT NULL,
    idMetodo_de_pago INT NOT NULL,
    monto           DECIMAL(10, 2) NOT NULL CHECK (monto >= 0),
    fecha_pago      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT pk_pago_empleado PRIMARY KEY (idPago_empleado),
    FOREIGN KEY (idEmpleado) REFERENCES EMPLEADO (idEmpleado),
    FOREIGN KEY (idMetodo_de_pago) REFERENCES METODO_DE_PAGO (idMetodo_de_pago)
);