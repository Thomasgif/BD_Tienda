-- ========================================================
-- DATOS DE PRUEBA E INICIALES PARA SUPABASE (POSTGRESQL)
-- Proyecto: BD_Tienda
-- ========================================================

-- 1. METODOS DE PAGO / CUENTAS
INSERT INTO METODO_DE_PAGO (nombre, num_cuenta, saldo) VALUES
('Efectivo (Caja Principal)', '0000', 5000000.00),
('Bancolombia Principal', '1234567890', 10000000.00),
('Nequi Empresa', '3001234567', 3000000.00)
ON CONFLICT (num_cuenta) DO NOTHING;

-- 2. EMPLEADOS (Gerente y Empleado de prueba)
-- Contraseña / documento para login:
-- Gerente: '0315' o '1010'
-- Empleado: '2709' o '2020'
INSERT INTO EMPLEADO (nombre, documento, trabajo_hora, pago_hora, telefono, correo, rol) VALUES
('Gerente Principal', '0315', 40.00, 25000.00, '3101112233', 'gerente@tienda.com', 1),
('Carlos Ruiz', '1010', 40.00, 15000.00, '3124445566', 'carlos@tienda.com', 0),
('Ana Lopez', '2709', 35.00, 15000.00, '3147778899', 'ana@tienda.com', 0)
ON CONFLICT (documento) DO NOTHING;

-- 3. PROVEEDORES
INSERT INTO PROVEEDOR (nombre, telefono, correo, estado, nit, direccion) VALUES
('SportMayorista S.A.S.', '3001112233', 'ventas@sportmayorista.com', TRUE, '900123456-1', 'Calle 10 # 20-30'),
('EliteFitness Distribuciones', '3104445566', 'pedidos@elitefitness.com', TRUE, '800654321-2', 'Av. 5 # 45-12'),
('Textiles Deportivos Col', '3209998877', 'contacto@textilesdep.com', TRUE, '901234567-3', 'Carrera 15 # 80-22')
ON CONFLICT (nombre) DO NOTHING;

-- 4. PRODUCTOS INICIALES
INSERT INTO PRODUCTO (nombre, referencia, precio_compra, precio_venta, bodega, descripción) VALUES
('Balon Futbol Pro', 'FB-01', 35000.00, 65000.00, 50, 'Balon No. 5 sintetico termofusionado'),
('Mancuerna 5kg Hex', 'GYM-01', 25000.00, 48000.00, 30, 'Mancuerna de hierro recubierta en neopreno'),
('Gafas Natacion HD', 'SW-01', 18000.00, 38000.00, 20, 'Gafas de silicona con proteccion UV y antiempanante'),
('Guantes Gimnasio', 'GYM-02', 15000.00, 32000.00, 40, 'Guantes de cuero sintetico con ajuste de muneca'),
('Banda Elastica Set', 'FIT-01', 12000.00, 28000.00, 60, 'Set x5 bandas elasticas de resistencia variada');

-- 5. CLIENTES DE PRUEBA
INSERT INTO CLIENTE (nombre, apellidos, documento, telefono, correo, direccion) VALUES
('Luis', 'Gomez Hernandez', '7777', '3005551122', 'luis.gomez@gmail.com', 'Calle 50 # 12-34'),
('Marta', 'Perez Rodriguez', '8888', '3216663344', 'marta.perez@hotmail.com', 'Carrera 7 # 45-67'),
('Juan', 'Restrepo Castro', '9999', '3157778899', 'juan.restrepo@outlook.com', 'Av. Bolivar # 10-20')
ON CONFLICT (documento) DO NOTHING;
