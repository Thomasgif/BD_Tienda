from database.base import db_cursor, _convertir_filas, SmartDict


def obtener_envios_list(rol=None):
    """Obtiene el histórico de envíos y recepciones de mercancía."""
    try:
        with db_cursor(commit=False, dictionary=True) as (cursor, _):
            consulta = """
                SELECT e.idEnvio, e.idCompra, e.fecha, e.valor, p.nombre AS proveedor,
                       e.idMetodo_de_pago, m.nombre AS metodo_pago, m.num_cuenta
                FROM ENVIO e
                JOIN COMPRA c ON e.idCompra = c.idCompra
                JOIN PROVEEDOR p ON c.idProveedor = p.idProveedor
                LEFT JOIN METODO_DE_PAGO m ON e.idMetodo_de_pago = m.idMetodo_de_pago
                ORDER BY e.fecha DESC, e.idEnvio DESC
            """
            cursor.execute(consulta)
            envios = cursor.fetchall()
            return _convertir_filas(envios) or []
    except Exception as e:
        raise Exception(f"Error al obtener envíos: {e}")


def insertar_envio(idCompra, idEmpleado, fecha, valor, idMetodo_de_pago, rol=None):
    """
    Registra el flete/envío de una compra, descuenta el saldo de la empresa,
    distribuye el costo de flete en el costo unitario del producto e incrementa el stock en bodega.
    """
    valor = float(valor)
    try:
        with db_cursor(commit=True, dictionary=True) as (cursor, _):
            # 1. Descontar del saldo de la cuenta
            cursor.execute(
                "UPDATE METODO_DE_PAGO SET saldo = saldo - %s WHERE idMetodo_de_pago = %s",
                (valor, idMetodo_de_pago)
            )

            # 2. Registrar el envío
            cursor.execute(
                """INSERT INTO ENVIO (idCompra, idEmpleado, fecha, valor, idMetodo_de_pago) 
                   VALUES (%s, %s, %s, %s, %s)""",
                (idCompra, idEmpleado, fecha, valor, idMetodo_de_pago)
            )

            # 3. Obtener detalles de la compra para ingresar al inventario
            cursor.execute("""
                SELECT dc.idProducto, dc.cantidad, p.precio_compra
                FROM DETALLE_COMPRA dc
                JOIN PRODUCTO p ON dc.idProducto = p.idProducto
                WHERE dc.idCompra = %s
            """, (idCompra,))
            detalles = cursor.fetchall()

            detalles_smart = _convertir_filas(detalles) or []
            total_unidades = sum(int(d['cantidad']) for d in detalles_smart)
            costo_envio_por_unidad = (valor / total_unidades) if total_unidades > 0 else 0.0

            # 4. Actualizar stock y precio de compra ponderado
            for d in detalles_smart:
                cant = int(d['cantidad'])
                precio_act = float(d['precio_compra'])
                nuevo_precio_compra = precio_act + costo_envio_por_unidad
                cursor.execute("""
                    UPDATE PRODUCTO 
                    SET bodega = bodega + %s, precio_compra = %s 
                    WHERE idProducto = %s
                """, (cant, nuevo_precio_compra, d['idProducto']))

    except Exception as e:
        err_msg = str(e).lower()
        if "check" in err_msg or "violates" in err_msg or "saldo" in err_msg:
            raise Exception("Saldo insuficiente en la cuenta para realizar el envío.")
        raise Exception(f"Error al registrar el envío: {e}")
