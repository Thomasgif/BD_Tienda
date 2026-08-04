from mysql.connector import Error
from math import isfinite
from database.base import obtener_conexion


def pago_total_venta(idventa, rol):
    conexion = None
    cursor = None
    try:
        conexion = obtener_conexion(rol)
        cursor = conexion.cursor(dictionary=True)
        cursor.execute("SELECT SUM(monto) FROM PAGO WHERE idVenta = %s", (idventa,))
        pago = cursor.fetchone()
        return pago['SUM(monto)'] if pago['SUM(monto)'] is not None else 0.00
    except Error as e:
        raise Exception(f"Error al obtener pago de venta: {e}")
    finally:
        if cursor is not None:
            cursor.close()
        if conexion is not None and conexion.is_connected():
            conexion.close()


def pagar_venta_pendiente(id_venta, id_cliente, id_metodo_pago, monto, rol):
    conexion = None
    cursor = None
    try:
        conexion = obtener_conexion(rol)
        cursor = conexion.cursor(dictionary=True)

        monto = float(monto)

        # Bloquear la venta mientras se calcula y registra el nuevo saldo.
        cursor.execute(
            "SELECT idCliente, valor_total, estado_pago FROM VENTA WHERE idVenta = %s FOR UPDATE",
            (id_venta,)
        )
        row = cursor.fetchone()
        if not row:
            raise Exception("La venta no existe.")
        if row['estado_pago'] != 'PENDIENTE':
            raise Exception("La venta ya no está pendiente.")
        if row['idCliente'] != id_cliente:
            raise Exception("La venta no pertenece al cliente seleccionado.")
        valor_total = float(row['valor_total'])

        # Validar que el monto no supere la deuda pendiente
        cursor.execute("SELECT COALESCE(SUM(monto), 0) AS pagado FROM PAGO WHERE idVenta = %s", (id_venta,))
        pagado_row = cursor.fetchone()
        ya_pagado = float(pagado_row['pagado'])
        pendiente = valor_total - ya_pagado

        if not isfinite(monto) or monto <= 0:
            raise Exception("El monto debe ser mayor a cero.")
        if monto > pendiente:
            raise Exception(f"El monto ingresado (${monto:,.2f}) supera la deuda pendiente (${pendiente:,.2f}).")

        # Registrar el pago
        cursor.execute(
            "INSERT INTO PAGO (idVenta, idMetodo_de_pago, monto, idCliente) VALUES (%s, %s, %s, %s)",
            (id_venta, id_metodo_pago, monto, id_cliente)
        )

        # Sumar al saldo del método de pago
        cursor.execute(
            "UPDATE METODO_DE_PAGO SET saldo = saldo + %s WHERE idMetodo_de_pago = %s",
            (monto, id_metodo_pago)
        )

        # Si con este pago se cubre el total, marcar como PAGADO
        nuevo_pagado = ya_pagado + monto
        if nuevo_pagado >= valor_total:
            cursor.execute(
                "UPDATE VENTA SET estado_pago = 'PAGADO' WHERE idVenta = %s",
                (id_venta,)
            )

        conexion.commit()
    except Exception as e:
        if conexion:
            conexion.rollback()
        raise Exception(f"{e}")
    finally:
        if cursor is not None: cursor.close()
        if conexion is not None and conexion.is_connected(): conexion.close()


def cancelar_venta(id_venta, rol):
    conexion = None
    cursor = None
    try:
        conexion = obtener_conexion(rol)
        cursor = conexion.cursor(dictionary=True)

        # Verificar que la venta esté en estado PENDIENTE
        cursor.execute("SELECT estado_pago FROM VENTA WHERE idVenta = %s", (id_venta,))
        venta = cursor.fetchone()
        if not venta:
            raise Exception("La venta no existe.")
        if venta['estado_pago'] != 'PENDIENTE':
            raise Exception(f"Solo se pueden cancelar ventas PENDIENTES. Estado actual: {venta['estado_pago']}")

        # Obtener los detalles para restaurar inventario
        cursor.execute(
            "SELECT idProducto, cantidad FROM DETALLE_VENTA WHERE idVenta = %s",
            (id_venta,)
        )
        detalles = cursor.fetchall()

        # Restaurar inventario de cada producto
        for det in detalles:
            cursor.execute(
                "UPDATE PRODUCTO SET bodega = bodega + %s WHERE idProducto = %s",
                (det['cantidad'], det['idProducto'])
            )

        # Cambiar estado de la venta a CANCELADO
        cursor.execute(
            "UPDATE VENTA SET estado_pago = 'CANCELADO' WHERE idVenta = %s",
            (id_venta,)
        )

        conexion.commit()
    except Exception as e:
        if conexion:
            conexion.rollback()
        raise Exception(f"{e}")
    finally:
        if cursor is not None: cursor.close()
        if conexion is not None and conexion.is_connected(): conexion.close()


def registrar_venta(id_empleado, id_cliente, productos, id_metodo_pago, monto_pagado, estado_pago, valor_total, rol):
    conexion = None
    cursor = None
    try:
        valor_total = float(valor_total)
        monto_pagado = float(monto_pagado)
        estado_pago = str(estado_pago).upper()

        if not isfinite(valor_total) or not isfinite(monto_pagado):
            raise Exception("Los valores monetarios no son válidos.")
        if estado_pago not in ('PAGADO', 'PENDIENTE'):
            raise Exception("El estado de pago no es válido.")
        if valor_total <= 0:
            raise Exception("El total de la venta debe ser mayor a cero.")
        if monto_pagado < 0 or monto_pagado > valor_total:
            raise Exception("El abono debe estar entre cero y el total de la venta.")
        if estado_pago == 'PAGADO' and monto_pagado != valor_total:
            raise Exception("Una venta PAGADA debe registrar el valor total.")
        if estado_pago == 'PENDIENTE' and monto_pagado >= valor_total:
            raise Exception("Una venta PENDIENTE debe conservar un saldo por pagar.")
        if monto_pagado > 0 and id_metodo_pago is None:
            raise Exception("Debe seleccionar un método de pago para registrar el abono.")

        conexion = obtener_conexion(rol)
        cursor = conexion.cursor()

        # 1. Insertar en VENTA
        consulta_venta = """
            INSERT INTO VENTA (idEmpleado, idCliente, estado_pago, valor_total)
            VALUES (%s, %s, %s, %s)
        """
        cursor.execute(consulta_venta, (id_empleado, id_cliente, estado_pago, valor_total))
        id_venta = cursor.lastrowid

        # 2. Insertar DETALLE_VENTA y actualizar bodega en PRODUCTO
        for prod in productos:
            id_prod = prod['idProducto']
            cantidad = prod['cantidad']

            # Insertar detalle
            cursor.execute(
                "INSERT INTO DETALLE_VENTA (idProducto, idVenta, cantidad) VALUES (%s, %s, %s)",
                (id_prod, id_venta, cantidad)
            )

            # Restar del inventario
            cursor.execute(
                "UPDATE PRODUCTO SET bodega = bodega - %s WHERE idProducto = %s",
                (cantidad, id_prod)
            )

        # 3. Si hay un pago (total o parcial), registrar en PAGO y actualizar METODO_DE_PAGO
        if id_metodo_pago is not None and monto_pagado > 0:
            cursor.execute(
                "INSERT INTO PAGO (idCliente, idVenta, idMetodo_de_pago, monto) VALUES (%s, %s, %s, %s)",
                (id_cliente, id_venta, id_metodo_pago, monto_pagado)
            )
            # Sumar al saldo de la cuenta de la empresa
            cursor.execute(
                "UPDATE METODO_DE_PAGO SET saldo = saldo + %s WHERE idMetodo_de_pago = %s",
                (monto_pagado, id_metodo_pago)
            )

        conexion.commit()
        return id_venta
    except Exception as e:
        if conexion:
            conexion.rollback()
        raise Exception(f"Error al registrar la venta: {e}")
    finally:
        if cursor is not None: cursor.close()
        if conexion is not None and conexion.is_connected(): conexion.close()


def obtener_ventas_cliente(id_cliente, rol):
    conexion = None
    cursor = None
    try:
        conexion = obtener_conexion(rol)
        cursor = conexion.cursor(dictionary=True)
        cursor.execute(
            "SELECT idVenta, fecha_venta, estado_pago, valor_total FROM VENTA WHERE idCliente = %s ORDER BY fecha_venta DESC", 
            (id_cliente,)
        )
        return cursor.fetchall()
    except Error as e:
        raise Exception(f"Error al obtener ventas del cliente: {e}")
    finally:
        if cursor is not None:
            cursor.close()
        if conexion is not None and conexion.is_connected():
            conexion.close()


def obtener_detalle_venta(id_venta, rol):
    conexion = None
    cursor = None
    try:
        conexion = obtener_conexion(rol)
        cursor = conexion.cursor(dictionary=True)
        consulta = """
            SELECT dv.idDetalle_venta, dv.idProducto, dv.cantidad, p.nombre, p.referencia, p.precio_venta
            FROM DETALLE_VENTA dv
            JOIN PRODUCTO p ON dv.idProducto = p.idProducto
            WHERE dv.idVenta = %s
        """
        cursor.execute(consulta, (id_venta,))
        return cursor.fetchall()
    except Error as e:
        raise Exception(f"Error al obtener detalle de venta: {e}")
    finally:
        if cursor is not None:
            cursor.close()
        if conexion is not None and conexion.is_connected():
            conexion.close()


def registrar_devolucion_cambio(id_venta, id_prod_devuelto, cant_devuelta, productos_nuevos, id_metodo_pago, monto_adicional, rol):
    conexion = None
    cursor = None
    try:
        conexion = obtener_conexion(rol)
        cursor = conexion.cursor(dictionary=True)

        # 1. Obtener detalles de la venta y del producto devuelto
        cursor.execute("SELECT idCliente, estado_pago, valor_total FROM VENTA WHERE idVenta = %s", (id_venta,))
        venta = cursor.fetchone()
        if not venta:
            raise Exception("La venta no existe.")
        id_cliente = venta['idCliente']

        # Verificar que el producto devuelto esté en el detalle y tenga suficiente cantidad
        cursor.execute(
            "SELECT cantidad FROM DETALLE_VENTA WHERE idVenta = %s AND idProducto = %s",
            (id_venta, id_prod_devuelto)
        )
        detalle_dev = cursor.fetchone()
        if not detalle_dev:
            raise Exception("El producto devuelto no pertenece a esta venta.")
        cant_vendida = int(detalle_dev['cantidad'])
        if cant_devuelta > cant_vendida:
            raise Exception(f"No puede devolver una cantidad ({cant_devuelta}) mayor a la vendida ({cant_vendida}).")

        # Obtener precio de venta del producto devuelto
        cursor.execute("SELECT precio_venta FROM PRODUCTO WHERE idProducto = %s", (id_prod_devuelto,))
        prod_dev_row = cursor.fetchone()
        if not prod_dev_row:
            raise Exception("El producto devuelto no existe en el catálogo.")
        precio_venta_dev = float(prod_dev_row['precio_venta'])

        # 2. Calcular valor del producto devuelto
        valor_devuelto = cant_devuelta * precio_venta_dev

        # 3. Calcular valor de los productos nuevos y validar stock
        valor_nuevos = 0.0
        for p_nuevo in productos_nuevos:
            id_p = p_nuevo['idProducto']
            cant_p = p_nuevo['cantidad']
            
            # Obtener datos del catálogo
            cursor.execute("SELECT precio_venta, bodega, nombre FROM PRODUCTO WHERE idProducto = %s", (id_p,))
            p_cat = cursor.fetchone()
            if not p_cat:
                raise Exception(f"El producto de reemplazo con ID {id_p} no existe.")
            
            precio_p = float(p_cat['precio_venta'])
            bodega_p = int(p_cat['bodega'])
            
            # Si el producto de reemplazo es el mismo que el devuelto, consideramos stock temporalmente devuelto
            stock_disponible = bodega_p
            if id_p == id_prod_devuelto:
                stock_disponible += cant_devuelta
                
            if cant_p > stock_disponible:
                raise Exception(f"No hay suficiente stock para el producto '{p_cat['nombre']}' (Solicitado: {cant_p}, Disponible: {stock_disponible}).")
            
            valor_nuevos += cant_p * precio_p

        # Validar regla de negocio: no se devuelve dinero, siempre se debe alcanzar el valor devuelto
        if round(valor_nuevos, 2) < round(valor_devuelto, 2):
            raise Exception(f"El valor de los nuevos artículos (${valor_nuevos:,.2f}) debe ser igual o mayor al valor del artículo devuelto (${valor_devuelto:,.2f}). No se devuelve dinero.")

        # 4. Modificar DETALLE_VENTA e inventario (PRODUCTO.bodega) para el devuelto
        if cant_devuelta == cant_vendida:
            # Eliminar del detalle
            cursor.execute("DELETE FROM DETALLE_VENTA WHERE idVenta = %s AND idProducto = %s", (id_venta, id_prod_devuelto))
        else:
            # Reducir cantidad
            cursor.execute(
                "UPDATE DETALLE_VENTA SET cantidad = cantidad - %s WHERE idVenta = %s AND idProducto = %s",
                (cant_devuelta, id_venta, id_prod_devuelto)
            )
        # Devolver a bodega
        cursor.execute("UPDATE PRODUCTO SET bodega = bodega + %s WHERE idProducto = %s", (cant_devuelta, id_prod_devuelto))

        # 5. Insertar/actualizar DETALLE_VENTA y restar de bodega para los nuevos
        for p_nuevo in productos_nuevos:
            id_p = p_nuevo['idProducto']
            cant_p = p_nuevo['cantidad']
            
            # Buscar si ya existe en el detalle de esta venta
            cursor.execute("SELECT cantidad FROM DETALLE_VENTA WHERE idVenta = %s AND idProducto = %s", (id_venta, id_p))
            det_p = cursor.fetchone()
            
            if det_p:
                cursor.execute(
                    "UPDATE DETALLE_VENTA SET cantidad = cantidad + %s WHERE idVenta = %s AND idProducto = %s",
                    (cant_p, id_venta, id_p)
                )
            else:
                cursor.execute(
                    "INSERT INTO DETALLE_VENTA (idVenta, idProducto, cantidad) VALUES (%s, %s, %s)",
                    (id_venta, id_p, cant_p)
                )
                
            # Restar de bodega
            cursor.execute("UPDATE PRODUCTO SET bodega = bodega - %s WHERE idProducto = %s", (cant_p, id_p))

        # 6. Actualizar el valor total de la venta
        diferencia_adicional = valor_nuevos - valor_devuelto
        if diferencia_adicional > 0:
            cursor.execute(
                "UPDATE VENTA SET valor_total = valor_total + %s WHERE idVenta = %s",
                (diferencia_adicional, id_venta)
            )
            # Si hay abono o pago de la diferencia
            if id_metodo_pago is not None and monto_adicional > 0:
                cursor.execute(
                    "INSERT INTO PAGO (idCliente, idVenta, idMetodo_de_pago, monto) VALUES (%s, %s, %s, %s)",
                    (id_cliente, id_venta, id_metodo_pago, monto_adicional)
                )
                cursor.execute(
                    "UPDATE METODO_DE_PAGO SET saldo = saldo + %s WHERE idMetodo_de_pago = %s",
                    (monto_adicional, id_metodo_pago)
                )
        elif diferencia_adicional < 0:
            pass

        # 7. Recalcular estado de pago
        cursor.execute("SELECT valor_total FROM VENTA WHERE idVenta = %s", (id_venta,))
        venta_actualizada = cursor.fetchone()
        nuevo_valor_total = float(venta_actualizada['valor_total'])

        cursor.execute("SELECT COALESCE(SUM(monto), 0) AS total_pagado FROM PAGO WHERE idVenta = %s", (id_venta,))
        pagos_row = cursor.fetchone()
        total_pagado = float(pagos_row['total_pagado'])

        if round(total_pagado, 2) >= round(nuevo_valor_total, 2):
            nuevo_estado = "PAGADO"
        else:
            nuevo_estado = "PENDIENTE"

        cursor.execute("UPDATE VENTA SET estado_pago = %s WHERE idVenta = %s", (nuevo_estado, id_venta))

        conexion.commit()
    except Exception as e:
        if conexion:
            conexion.rollback()
        raise Exception(f"Error al registrar la devolución/cambio: {e}")
    finally:
        if cursor is not None:
            cursor.close()
        if conexion is not None and conexion.is_connected():
            conexion.close()
