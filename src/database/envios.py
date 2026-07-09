from mysql.connector import Error
from database.base import obtener_conexion


def obtener_envios_list(rol):
    conexion = None
    cursor = None
    try:
        conexion = obtener_conexion(rol)
        cursor = conexion.cursor(dictionary=True)
        consulta = """
            SELECT e.idEnvio, e.idCompra, e.fecha, e.valor, p.nombre AS proveedor,
                   e.idMetodo_de_pago, m.nombre AS metodo_pago, m.num_cuenta
            FROM ENVIO e
            JOIN COMPRA c ON e.idCompra = c.idCompra
            JOIN PROVEEDOR p ON c.idProveedor = p.idProveedor
            LEFT JOIN METODO_DE_PAGO m ON e.idMetodo_de_pago = m.idMetodo_de_pago
            ORDER BY e.fecha DESC
        """
        cursor.execute(consulta)
        return cursor.fetchall()
    except Exception as e:
        raise Exception(f"Error al obtener envíos: {e}")
    finally:
        if cursor is not None: cursor.close()
        if conexion is not None and conexion.is_connected(): conexion.close()


def insertar_envio(idCompra, idEmpleado, fecha, valor, idMetodo_de_pago, rol):
    conexion = None
    cursor = None
    try:
        conexion = obtener_conexion(rol)
        cursor = conexion.cursor()
        
        # Restar del saldo de la cuenta
        cursor.execute(
            "UPDATE METODO_DE_PAGO SET saldo = saldo - %s WHERE idMetodo_de_pago = %s",
            (valor, idMetodo_de_pago)
        )
        
        consulta = "INSERT INTO ENVIO (idCompra, idEmpleado, fecha, valor, idMetodo_de_pago) VALUES (%s, %s, %s, %s, %s)"
        cursor.execute(consulta, (idCompra, idEmpleado, fecha, valor, idMetodo_de_pago))
        
        # Actualizar stock (bodega) y ajustar precio_compra de los productos comprados
        # 1. Obtener detalles de la compra (idProducto, cantidad, precio_compra actual)
        cursor.execute("""
            SELECT dc.idProducto, dc.cantidad, p.precio_compra
            FROM DETALLE_COMPRA dc
            JOIN PRODUCTO p ON dc.idProducto = p.idProducto
            WHERE dc.idCompra = %s
        """, (idCompra,))
        detalles = cursor.fetchall()
        
        # 2. Calcular total de unidades
        total_unidades = sum(d[1] for d in detalles)
        if total_unidades > 0:
            costo_envio_por_unidad = float(valor) / total_unidades
        else:
            costo_envio_por_unidad = 0.0
            
        # 3. Actualizar cada producto
        for id_prod, cant, precio_act in detalles:
            nuevo_precio_compra = float(precio_act) + costo_envio_por_unidad
            cursor.execute("""
                UPDATE PRODUCTO 
                SET bodega = bodega + %s, precio_compra = %s 
                WHERE idProducto = %s
            """, (cant, nuevo_precio_compra, id_prod))
            
        conexion.commit()
    except Error as e:
        if conexion:
            conexion.rollback()
        if e.errno == 3819 or "CONSTRAINT" in str(e).upper() or "check constraint" in str(e).lower():
            raise Exception("Saldo insuficiente en la cuenta para realizar el envío.")
        raise Exception(f"Error al registrar el envío: {e}")
    except Exception as e:
        if conexion:
            conexion.rollback()
        raise e
    finally:
        if cursor is not None: cursor.close()
        if conexion is not None and conexion.is_connected(): conexion.close()
