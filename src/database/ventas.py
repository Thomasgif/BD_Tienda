from math import isfinite
from psycopg2.extras import execute_values
from database.base import db_cursor, _convertir_filas, SmartDict


def pago_total_venta(idventa, rol=None):
    """Retorna el monto total pagado/abonado a una venta específica."""
    try:
        with db_cursor(commit=False, dictionary=True) as (cursor, _):
            cursor.execute("SELECT COALESCE(SUM(monto), 0) AS total_pagado FROM PAGO WHERE idVenta = %s", (idventa,))
            pago = cursor.fetchone()
            return float(pago['total_pagado']) if pago and 'total_pagado' in pago else 0.00
    except Exception as e:
        raise Exception(f"Error al obtener pago de venta: {e}")


def pagar_venta_pendiente(id_venta, id_cliente, id_metodo_pago, monto, rol=None):
    """Registra un abono o liquidación total a una venta a crédito/pendiente."""
    monto = float(monto)
    if not isfinite(monto) or monto <= 0:
        raise Exception("El monto debe ser mayor a cero.")

    try:
        with db_cursor(commit=True, dictionary=True) as (cursor, _):
            # 1. Bloquear y verificar la venta
            cursor.execute(
                "SELECT idCliente, valor_total, estado_pago FROM VENTA WHERE idVenta = %s FOR UPDATE",
                (id_venta,)
            )
            row = cursor.fetchone()
            if not row:
                raise Exception("La venta no existe.")
            
            row = SmartDict(row)
            if row['estado_pago'] != 'PENDIENTE':
                raise Exception("La venta ya no está pendiente.")
            if row['idCliente'] != id_cliente:
                raise Exception("La venta no pertenece al cliente seleccionado.")
            
            valor_total = float(row['valor_total'])

            # 2. Validar que el monto no supere la deuda pendiente
            cursor.execute("SELECT COALESCE(SUM(monto), 0) AS pagado FROM PAGO WHERE idVenta = %s", (id_venta,))
            pagado_row = cursor.fetchone()
            ya_pagado = float(pagado_row['pagado'] if pagado_row and 'pagado' in pagado_row else 0)
            pendiente = valor_total - ya_pagado

            if monto > (pendiente + 0.01): # Margen de redondeo
                raise Exception(f"El monto ingresado (${monto:,.2f}) supera la deuda pendiente (${pendiente:,.2f}).")

            # 3. Registrar el pago
            cursor.execute(
                "INSERT INTO PAGO (idVenta, idMetodo_de_pago, monto, idCliente) VALUES (%s, %s, %s, %s)",
                (id_venta, id_metodo_pago, monto, id_cliente)
            )

            # 4. Sumar al saldo del método de pago
            cursor.execute(
                "UPDATE METODO_DE_PAGO SET saldo = saldo + %s WHERE idMetodo_de_pago = %s",
                (monto, id_metodo_pago)
            )

            # 5. Si se liquida la deuda, actualizar estado de la venta
            nuevo_pagado = ya_pagado + monto
            if nuevo_pagado >= (valor_total - 0.01):
                cursor.execute(
                    "UPDATE VENTA SET estado_pago = 'PAGADO' WHERE idVenta = %s",
                    (id_venta,)
                )
    except Exception as e:
        raise Exception(f"{e}")


def cancelar_venta(id_venta, rol=None):
    """Cancela una venta pendiente restaurando el stock de productos."""
    try:
        with db_cursor(commit=True, dictionary=True) as (cursor, _):
            # 1. Verificar estado de la venta
            cursor.execute("SELECT estado_pago FROM VENTA WHERE idVenta = %s FOR UPDATE", (id_venta,))
            venta = cursor.fetchone()
            if not venta:
                raise Exception("La venta no existe.")
            
            venta = SmartDict(venta)
            if venta['estado_pago'] != 'PENDIENTE':
                raise Exception(f"Solo se pueden cancelar ventas PENDIENTES. Estado actual: {venta['estado_pago']}")

            # 2. Obtener productos para restaurar stock
            cursor.execute(
                "SELECT idProducto, cantidad FROM DETALLE_VENTA WHERE idVenta = %s",
                (id_venta,)
            )
            detalles = cursor.fetchall()

            # 3. Restaurar inventario
            for det in _convertir_filas(detalles):
                cursor.execute(
                    "UPDATE PRODUCTO SET bodega = bodega + %s WHERE idProducto = %s",
                    (det['cantidad'], det['idProducto'])
                )

            # 4. Marcar venta como cancelada
            cursor.execute(
                "UPDATE VENTA SET estado_pago = 'CANCELADO' WHERE idVenta = %s",
                (id_venta,)
            )
    except Exception as e:
        raise Exception(f"{e}")


def registrar_venta(id_empleado, id_cliente, productos, id_metodo_pago, monto_pagado, estado_pago, valor_total, rol=None):
    """
    Registra una venta completa con sus detalles, pagos y ajuste de inventario
    en una sola transacción atómica de alto rendimiento.
    """
    valor_total = float(valor_total)
    monto_pagado = float(monto_pagado)
    estado_pago = str(estado_pago).upper()

    if not isfinite(valor_total) or not isfinite(monto_pagado):
        raise Exception("Los valores monetarios no son válidos.")
    if estado_pago not in ('PAGADO', 'PENDIENTE'):
        raise Exception("El estado de pago no es válido.")
    if valor_total <= 0:
        raise Exception("El total de la venta debe ser mayor a cero.")
    if monto_pagado < 0 or monto_pagado > (valor_total + 0.01):
        raise Exception("El abono debe estar entre cero y el total de la venta.")
    if estado_pago == 'PAGADO' and round(monto_pagado, 2) != round(valor_total, 2):
        raise Exception("Una venta PAGADA debe registrar el valor total.")
    if estado_pago == 'PENDIENTE' and round(monto_pagado, 2) >= round(valor_total, 2):
        raise Exception("Una venta PENDIENTE debe conservar un saldo por pagar.")
    if monto_pagado > 0 and id_metodo_pago is None:
        raise Exception("Debe seleccionar un método de pago para registrar el abono.")

    try:
        with db_cursor(commit=True, dictionary=True) as (cursor, _):
            # 1. Insertar cabecera de VENTA
            cursor.execute("""
                INSERT INTO VENTA (idEmpleado, idCliente, estado_pago, valor_total)
                VALUES (%s, %s, %s, %s)
                RETURNING idVenta
            """, (id_empleado, id_cliente, estado_pago, valor_total))
            
            res_venta = cursor.fetchone()
            id_venta = res_venta['idventa'] if res_venta and 'idventa' in res_venta else res_venta['idVenta']

            # 2. Inserción múltiple de detalles y descuento de inventario
            detalles_tuples = [(p['idProducto'], id_venta, p['cantidad']) for p in productos]
            execute_values(
                cursor,
                "INSERT INTO DETALLE_VENTA (idProducto, idVenta, cantidad) VALUES %s",
                detalles_tuples
            )

            # Restar stock de cada producto
            for prod in productos:
                cursor.execute(
                    "UPDATE PRODUCTO SET bodega = bodega - %s WHERE idProducto = %s",
                    (prod['cantidad'], prod['idProducto'])
                )

            # 3. Si hay un pago inicial (abono o pago total), registrar en PAGO y actualizar cuenta
            if id_metodo_pago is not None and monto_pagado > 0:
                cursor.execute(
                    "INSERT INTO PAGO (idCliente, idVenta, idMetodo_de_pago, monto) VALUES (%s, %s, %s, %s)",
                    (id_cliente, id_venta, id_metodo_pago, monto_pagado)
                )
                cursor.execute(
                    "UPDATE METODO_DE_PAGO SET saldo = saldo + %s WHERE idMetodo_de_pago = %s",
                    (monto_pagado, id_metodo_pago)
                )

            return id_venta
    except Exception as e:
        raise Exception(f"Error al registrar la venta: {e}")


def obtener_ventas_cliente(id_cliente, rol=None):
    """Obtiene el historial de ventas asociadas a un cliente específico."""
    try:
        with db_cursor(commit=False, dictionary=True) as (cursor, _):
            cursor.execute("""
                SELECT idVenta, fecha_venta, estado_pago, valor_total 
                FROM VENTA 
                WHERE idCliente = %s 
                ORDER BY fecha_venta DESC
            """, (id_cliente,))
            ventas = cursor.fetchall()
            return _convertir_filas(ventas) or []
    except Exception as e:
        raise Exception(f"Error al obtener ventas del cliente: {e}")


def obtener_detalle_venta(id_venta, rol=None):
    """Obtiene los productos y cantidades incluidos en una venta determinada."""
    try:
        with db_cursor(commit=False, dictionary=True) as (cursor, _):
            cursor.execute("""
                SELECT dv.idDetalle_venta, dv.idProducto, dv.cantidad, p.nombre, p.referencia, p.precio_venta
                FROM DETALLE_VENTA dv
                JOIN PRODUCTO p ON dv.idProducto = p.idProducto
                WHERE dv.idVenta = %s
            """, (id_venta,))
            detalles = cursor.fetchall()
            return _convertir_filas(detalles) or []
    except Exception as e:
        raise Exception(f"Error al obtener detalle de venta: {e}")


def registrar_devolucion_cambio(id_venta, id_prod_devuelto, cant_devuelta, productos_nuevos, id_metodo_pago, monto_adicional, rol=None):
    """
    Procesa una devolución / cambio de productos en Supabase asegurando consistencia atómica
    y validación estricta de inventario y saldos.
    """
    try:
        with db_cursor(commit=True, dictionary=True) as (cursor, _):
            # 1. Obtener detalles de la venta y del producto devuelto
            cursor.execute("SELECT idCliente, estado_pago, valor_total FROM VENTA WHERE idVenta = %s FOR UPDATE", (id_venta,))
            venta = cursor.fetchone()
            if not venta:
                raise Exception("La venta no existe.")
            venta = SmartDict(venta)
            id_cliente = venta['idCliente']

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

            # Precio del producto devuelto
            cursor.execute("SELECT precio_venta FROM PRODUCTO WHERE idProducto = %s", (id_prod_devuelto,))
            prod_dev_row = cursor.fetchone()
            if not prod_dev_row:
                raise Exception("El producto devuelto no existe en el catálogo.")
            precio_venta_dev = float(prod_dev_row['precio_venta'])
            valor_devuelto = cant_devuelta * precio_venta_dev

            # 2. Validar productos nuevos
            valor_nuevos = 0.0
            for p_nuevo in productos_nuevos:
                id_p = p_nuevo['idProducto']
                cant_p = p_nuevo['cantidad']
                
                cursor.execute("SELECT precio_venta, bodega, nombre FROM PRODUCTO WHERE idProducto = %s", (id_p,))
                p_cat = cursor.fetchone()
                if not p_cat:
                    raise Exception(f"El producto de reemplazo con ID {id_p} no existe.")
                
                p_cat = SmartDict(p_cat)
                precio_p = float(p_cat['precio_venta'])
                bodega_p = int(p_cat['bodega'])
                
                stock_disponible = bodega_p + (cant_devuelta if id_p == id_prod_devuelto else 0)
                if cant_p > stock_disponible:
                    raise Exception(f"No hay suficiente stock para el producto '{p_cat['nombre']}' (Solicitado: {cant_p}, Disponible: {stock_disponible}).")
                
                valor_nuevos += cant_p * precio_p

            if round(valor_nuevos, 2) < round(valor_devuelto, 2):
                raise Exception(f"El valor de los nuevos artículos (${valor_nuevos:,.2f}) debe ser igual o mayor al valor del artículo devuelto (${valor_devuelto:,.2f}). No se devuelve dinero.")

            # 3. Modificar DETALLE_VENTA y stock para el devuelto
            if cant_devuelta == cant_vendida:
                cursor.execute("DELETE FROM DETALLE_VENTA WHERE idVenta = %s AND idProducto = %s", (id_venta, id_prod_devuelto))
            else:
                cursor.execute(
                    "UPDATE DETALLE_VENTA SET cantidad = cantidad - %s WHERE idVenta = %s AND idProducto = %s",
                    (cant_devuelta, id_venta, id_prod_devuelto)
                )
            cursor.execute("UPDATE PRODUCTO SET bodega = bodega + %s WHERE idProducto = %s", (cant_devuelta, id_prod_devuelto))

            # 4. Insertar/actualizar DETALLE_VENTA y descontar stock para los nuevos
            for p_nuevo in productos_nuevos:
                id_p = p_nuevo['idProducto']
                cant_p = p_nuevo['cantidad']
                
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
                cursor.execute("UPDATE PRODUCTO SET bodega = bodega - %s WHERE idProducto = %s", (cant_p, id_p))

            # 5. Ajustar valor total de la venta si hubo excedente
            diferencia_adicional = valor_nuevos - valor_devuelto
            if diferencia_adicional > 0:
                cursor.execute(
                    "UPDATE VENTA SET valor_total = valor_total + %s WHERE idVenta = %s",
                    (diferencia_adicional, id_venta)
                )
                if id_metodo_pago is not None and monto_adicional > 0:
                    cursor.execute(
                        "INSERT INTO PAGO (idCliente, idVenta, idMetodo_de_pago, monto) VALUES (%s, %s, %s, %s)",
                        (id_cliente, id_venta, id_metodo_pago, monto_adicional)
                    )
                    cursor.execute(
                        "UPDATE METODO_DE_PAGO SET saldo = saldo + %s WHERE idMetodo_de_pago = %s",
                        (monto_adicional, id_metodo_pago)
                    )

            # 6. Recalcular estado de pago
            cursor.execute("SELECT valor_total FROM VENTA WHERE idVenta = %s", (id_venta,))
            venta_actualizada = cursor.fetchone()
            nuevo_valor_total = float(venta_actualizada['valor_total'])

            cursor.execute("SELECT COALESCE(SUM(monto), 0) AS total_pagado FROM PAGO WHERE idVenta = %s", (id_venta,))
            pagos_row = cursor.fetchone()
            total_pagado = float(pagos_row['total_pagado'])

            nuevo_estado = "PAGADO" if round(total_pagado, 2) >= round(nuevo_valor_total, 2) else "PENDIENTE"
            cursor.execute("UPDATE VENTA SET estado_pago = %s WHERE idVenta = %s", (nuevo_estado, id_venta))

    except Exception as e:
        raise Exception(f"Error al registrar la devolución/cambio: {e}")
