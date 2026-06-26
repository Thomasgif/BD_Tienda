CREATE USER 'gerente'@'localhost' IDENTIFIED BY '0315';
CREATE USER 'log'@'localhost' IDENTIFIED BY '123456';
CREATE USER 'empleado'@'localhost' IDENTIFIED BY '2709';

GRANT SELECT ON BD_Tienda.EMPLEADO TO 'log'@'localhost';

GRANT SELECT, INSERT, UPDATE, DELETE ON BD_Tienda.CLIENTE TO 'gerente'@'localhost';
GRANT SELECT, INSERT ON BD_Tienda.DETALLE_COMPRA TO 'gerente'@'localhost';
GRANT SELECT ON BD_Tienda.DETALLE_VENTA TO 'gerente'@'localhost';
GRANT SELECT, INSERT, UPDATE, DELETE ON BD_Tienda.EMPLEADO TO 'gerente'@'localhost';
GRANT SELECT, INSERT, UPDATE, DELETE ON BD_Tienda.CUENTA_EMPRESA TO 'gerente'@'localhost';
GRANT SELECT, INSERT, UPDATE, DELETE ON BD_Tienda.METODO_DE_PAGO TO 'gerente'@'localhost';
GRANT SELECT, INSERT, UPDATE, DELETE ON BD_Tienda.PAGO TO 'gerente'@'localhost';
GRANT SELECT, INSERT, UPDATE, DELETE ON BD_Tienda.PRODUCTO TO 'gerente'@'localhost';
GRANT SELECT, INSERT, UPDATE, DELETE ON BD_Tienda.PROVEEDOR TO 'gerente'@'localhost';
GRANT SELECT, INSERT, UPDATE, DELETE ON BD_Tienda.VENTA TO 'gerente'@'localhost';
GRANT SELECT, INSERT, UPDATE, DELETE ON BD_Tienda.COMPRA TO 'gerente'@'localhost';
GRANT SELECT, INSERT, UPDATE, DELETE ON BD_Tienda.ENVIO TO 'gerente'@'localhost';
GRANT SELECT, INSERT, UPDATE, DELETE ON BD_Tienda.PAGO_EMPLEADO TO 'gerente'@'localhost';
GRANT SELECT, INSERT, UPDATE, DELETE ON BD_Tienda.GASTO TO 'gerente'@'localhost';


GRANT SELECT, INSERT, UPDATE ON BD_Tienda.CLIENTE TO 'empleado'@'localhost';
GRANT SELECT ON BD_Tienda.COMPRA TO 'empleado'@'localhost';
GRANT SELECT ON BD_Tienda.CUENTA_EMPRESA TO 'empleado'@'localhost';
GRANT SELECT ON BD_Tienda.DETALLE_COMPRA TO 'empleado'@'localhost';
GRANT SELECT ON BD_Tienda.DETALLE_VENTA TO 'empleado'@'localhost';
GRANT SELECT, INSERT, UPDATE ON BD_Tienda.ENVIO TO 'empleado'@'localhost';
GRANT SELECT, UPDATE ON BD_Tienda.METODO_DE_PAGO TO 'empleado'@'localhost';
GRANT SELECT, INSERT ON BD_Tienda.PAGO TO 'empleado'@'localhost';
GRANT SELECT, INSERT, UPDATE ON BD_Tienda.PRODUCTO TO 'empleado'@'localhost';
GRANT SELECT ON BD_Tienda.PROVEEDOR TO 'empleado'@'localhost';
GRANT SELECT, INSERT, UPDATE, DELETE ON BD_Tienda.VENTA TO 'empleado'@'localhost';
