-- ========================================================
-- ESQUEMA DE BASE DE DATOS PARA SUPABASE (POSTGRESQL)
-- Proyecto: BD_Tienda - Sistema de Gestión y Ventas
-- ========================================================

-- 1. PROVEEDOR
CREATE TABLE IF NOT EXISTS PROVEEDOR (
    idProveedor SERIAL PRIMARY KEY,
    nombre VARCHAR(50) NOT NULL UNIQUE,
    telefono VARCHAR(20) NULL UNIQUE,
    correo VARCHAR(50) NULL,
    estado BOOLEAN DEFAULT TRUE,
    nit VARCHAR(20) NULL,
    direccion VARCHAR(100) NULL
);

-- 2. PRODUCTO
CREATE TABLE IF NOT EXISTS PRODUCTO (
    idProducto SERIAL PRIMARY KEY,
    nombre VARCHAR(50) NOT NULL,
    referencia VARCHAR(50) NOT NULL,
    precio_compra NUMERIC(10, 2) NOT NULL CHECK (precio_compra >= 0),
    precio_venta NUMERIC(10, 2) NOT NULL CHECK (precio_venta >= 0),
    bodega INT NOT NULL DEFAULT 0 CHECK (bodega >= 0),
    descripción VARCHAR(255) NOT NULL
);

-- 3. EMPLEADO
CREATE TABLE IF NOT EXISTS EMPLEADO (
    idEmpleado SERIAL PRIMARY KEY,
    nombre VARCHAR(50) NOT NULL,
    documento VARCHAR(20) NOT NULL UNIQUE,
    trabajo_hora NUMERIC(10, 2) NOT NULL DEFAULT 0 CHECK (trabajo_hora >= 0),
    pago_hora NUMERIC(10, 2) NOT NULL CHECK (pago_hora >= 0),
    telefono VARCHAR(20) NULL,
    correo VARCHAR(50) NULL,
    rol SMALLINT NOT NULL DEFAULT 0 -- 0: Empleado, 1: Gerente
);

-- 4. METODO_DE_PAGO (Cuentas de la empresa)
CREATE TABLE IF NOT EXISTS METODO_DE_PAGO (
    idMetodo_de_pago SERIAL PRIMARY KEY,
    nombre VARCHAR(50) NOT NULL,
    num_cuenta VARCHAR(30) NOT NULL UNIQUE,
    saldo NUMERIC(10, 2) NOT NULL DEFAULT 0 CHECK (saldo >= 0)
);

-- 5. CLIENTE
CREATE TABLE IF NOT EXISTS CLIENTE (
    idCliente SERIAL PRIMARY KEY,
    nombre VARCHAR(50) NOT NULL,
    apellidos VARCHAR(50) NOT NULL,
    documento VARCHAR(20) NOT NULL UNIQUE,
    telefono VARCHAR(20) NULL,
    correo VARCHAR(50) NULL,
    direccion VARCHAR(100) NULL
);

-- 6. COMPRA (Abastecimiento a proveedores)
CREATE TABLE IF NOT EXISTS COMPRA (
    idCompra SERIAL PRIMARY KEY,
    idEmpleado INT REFERENCES EMPLEADO (idEmpleado) ON DELETE SET NULL,
    idProveedor INT REFERENCES PROVEEDOR (idProveedor) ON DELETE RESTRICT,
    idMetodo_de_pago INT REFERENCES METODO_DE_PAGO (idMetodo_de_pago) ON DELETE RESTRICT,
    total NUMERIC(10, 2) NOT NULL DEFAULT 0 CHECK (total >= 0),
    fechacompra TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- 7. DETALLE_COMPRA
CREATE TABLE IF NOT EXISTS DETALLE_COMPRA (
    idDetalle_compra SERIAL PRIMARY KEY,
    idProducto INT NOT NULL REFERENCES PRODUCTO (idProducto) ON DELETE RESTRICT,
    idCompra INT NOT NULL REFERENCES COMPRA (idCompra) ON DELETE CASCADE,
    cantidad INT NOT NULL CHECK (cantidad > 0),
    precio_unit NUMERIC(10, 2) NOT NULL DEFAULT 0 CHECK (precio_unit >= 0)
);

-- 8. VENTA
CREATE TABLE IF NOT EXISTS VENTA (
    idVenta SERIAL PRIMARY KEY,
    idEmpleado INT REFERENCES EMPLEADO (idEmpleado) ON DELETE SET NULL,
    idCliente INT REFERENCES CLIENTE (idCliente) ON DELETE RESTRICT,
    fecha_venta TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    estado_pago VARCHAR(20) NOT NULL CHECK (estado_pago IN ('PAGADO', 'PENDIENTE', 'CANCELADO')),
    valor_total NUMERIC(10, 2) NOT NULL CHECK (valor_total >= 0)
);

-- 9. DETALLE_VENTA
CREATE TABLE IF NOT EXISTS DETALLE_VENTA (
    idDetalle_venta SERIAL PRIMARY KEY,
    idProducto INT NOT NULL REFERENCES PRODUCTO (idProducto) ON DELETE RESTRICT,
    idVenta INT NOT NULL REFERENCES VENTA (idVenta) ON DELETE CASCADE,
    cantidad INT NOT NULL CHECK (cantidad > 0)
);

-- 10. PAGO (Cobros recibidos de clientes)
CREATE TABLE IF NOT EXISTS PAGO (
    idPago SERIAL PRIMARY KEY,
    idCliente INT REFERENCES CLIENTE (idCliente) ON DELETE RESTRICT,
    idVenta INT REFERENCES VENTA (idVenta) ON DELETE CASCADE,
    idMetodo_de_pago INT REFERENCES METODO_DE_PAGO (idMetodo_de_pago) ON DELETE RESTRICT,
    monto NUMERIC(10, 2) NOT NULL CHECK (monto >= 0),
    fecha_pago TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 11. ENVIO (Fletes y recepción de compras de proveedores)
CREATE TABLE IF NOT EXISTS ENVIO (
    idEnvio SERIAL PRIMARY KEY,
    idCompra INT NOT NULL UNIQUE REFERENCES COMPRA (idCompra) ON DELETE CASCADE,
    idEmpleado INT NOT NULL REFERENCES EMPLEADO (idEmpleado) ON DELETE RESTRICT,
    idMetodo_de_pago INT REFERENCES METODO_DE_PAGO (idMetodo_de_pago) ON DELETE RESTRICT,
    fecha DATE DEFAULT CURRENT_DATE,
    valor NUMERIC(10, 2) NOT NULL CHECK (valor >= 0)
);

-- 12. PAGO_EMPLEADO (Nómina)
CREATE TABLE IF NOT EXISTS PAGO_EMPLEADO (
    idPago_empleado SERIAL PRIMARY KEY,
    idEmpleado INT NOT NULL REFERENCES EMPLEADO (idEmpleado) ON DELETE RESTRICT,
    idMetodo_de_pago INT NOT NULL REFERENCES METODO_DE_PAGO (idMetodo_de_pago) ON DELETE RESTRICT,
    monto NUMERIC(10, 2) NOT NULL CHECK (monto >= 0),
    fecha_pago TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 13. GASTO (Gastos operativos generales)
CREATE TABLE IF NOT EXISTS GASTO (
    idGasto SERIAL PRIMARY KEY,
    idMetodo_de_pago INT NOT NULL REFERENCES METODO_DE_PAGO (idMetodo_de_pago) ON DELETE RESTRICT,
    descripción VARCHAR(200) NOT NULL,
    monto NUMERIC(10, 2) NOT NULL CHECK (monto >= 0),
    fecha TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ========================================================
-- ÍNDICES OPTIMIZADOS PARA RENDIMIENTO Y BAJA LATENCIA
-- ========================================================
CREATE INDEX IF NOT EXISTS idx_venta_cliente ON VENTA (idCliente);
CREATE INDEX IF NOT EXISTS idx_venta_fecha ON VENTA (fecha_venta);
CREATE INDEX IF NOT EXISTS idx_venta_estado ON VENTA (estado_pago);

CREATE INDEX IF NOT EXISTS idx_detalle_venta_venta ON DETALLE_VENTA (idVenta);
CREATE INDEX IF NOT EXISTS idx_detalle_venta_prod ON DETALLE_VENTA (idProducto);

CREATE INDEX IF NOT EXISTS idx_pago_venta ON PAGO (idVenta);
CREATE INDEX IF NOT EXISTS idx_pago_fecha ON PAGO (fecha_pago);
CREATE INDEX IF NOT EXISTS idx_pago_cliente ON PAGO (idCliente);

CREATE INDEX IF NOT EXISTS idx_compra_proveedor ON COMPRA (idProveedor);
CREATE INDEX IF NOT EXISTS idx_compra_fecha ON COMPRA (fechacompra);
CREATE INDEX IF NOT EXISTS idx_detalle_compra_compra ON DETALLE_COMPRA (idCompra);

CREATE INDEX IF NOT EXISTS idx_envio_compra ON ENVIO (idCompra);
CREATE INDEX IF NOT EXISTS idx_envio_fecha ON ENVIO (fecha);

CREATE INDEX IF NOT EXISTS idx_gasto_fecha ON GASTO (fecha);
CREATE INDEX IF NOT EXISTS idx_pago_empleado_fecha ON PAGO_EMPLEADO (fecha_pago);
