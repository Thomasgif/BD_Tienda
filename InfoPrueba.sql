USE BD_Tienda;

-- 1. PROVEEDORES (Nombres cortos por tu restricción VARCHAR(20))
INSERT INTO PROVEEDOR (nombre, telefono, correo, estado, nit, direccion) VALUES
('SportMayorista', '3001112233', 'ventas@sport.com', 1, '900-1', 'Calle 10'),
('EliteFitness', '3104445566', 'info@elite.com', 1, '800-2', 'Av. 5');

-- 2. PRODUCTOS (Deportes)
INSERT INTO PRODUCTO (nombre, referencia, precio_compra, precio_venta, bodega, descripcion) VALUES
('Balon Futbol', 'FB-01', 15.00, 30.00, 50, 'Balon N5 sintetico'),
('Mancuerna 5kg', 'GYM-01', 10.00, 20.00, 30, 'Hierro neopreno'),
('Gafas Natacion', 'SW-01', 8.00, 18.00, 20, 'Anti-empañante');

-- 3. EMPLEADOS
INSERT INTO EMPLEADO (nombre, documento, trabajo_hora, pago_hora, telefono, correo) VALUES
('Carlos Ruiz', '1010', 40.00, 15.00, '312', 'carlos@tienda.com'),
('Ana Lopez', '2020', 35.00, 15.00, '314', 'ana@tienda.com');

-- 4. CLIENTES
INSERT INTO CLIENTE (nombre, apellidos, documento, telefono, correo, direccion) VALUES
('Luis', 'Gomez', '7777', '300', 'luis@mail.com', 'Calle A'),
('Marta', 'Perez', '8888', '321', 'marta@mail.com', 'Calle B');

-- 5. METODOS DE PAGO
INSERT INTO METODO_DE_PAGO (nombre, num_cuenta) VALUES
('Efectivo', '0000'),
('Tarjeta', '12345678');

-- 6. COMPRA (Abastecimiento de Balones)
INSERT INTO COMPRA (idEmpleado, idProveedor) VALUES (1, 1);
INSERT INTO DETALLE_COMPRA (idProducto, idCompra, cantidad) VALUES (1, 1, 10);

-- 7. VENTA (Venta de una Mancuerna y Gafas)
-- El valor_total es 20 + 18 = 38
INSERT INTO VENTA (idEmpleado, estado_pago, valor_total) VALUES (2, 'PAGADO', 38.00);

-- 8. DETALLE DE VENTA
INSERT INTO DETALLE_VENTA (idProducto, idVenta, cantidad) VALUES 
(2, 1, 1), -- 1 Mancuerna
(3, 1, 1); -- 1 Gafas

-- 9. PAGO DE LA VENTA
INSERT INTO PAGO (idCliente, idVenta, idMetodo_de_pago, monto) VALUES (1, 1, 2, 38.00);