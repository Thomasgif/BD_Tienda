from mysql.connector import Error
from database.base import obtener_conexion


def obtener_saldos_cuentas(rol):
    conexion = None
    cursor = None
    try:
        conexion = obtener_conexion(rol)
        cursor = conexion.cursor(dictionary=True)
        consulta = """
            SELECT 
                idMetodo_de_pago,
                nombre AS tipo_cuenta, 
                num_cuenta, 
                saldo AS saldo_total
            FROM METODO_DE_PAGO
        """
        cursor.execute(consulta)
        cuentas = cursor.fetchall()
        return cuentas
    except Error as e:
        raise Exception(f"Error al obtener saldos de cuentas: {e}")
    finally:
        if cursor is not None:
            cursor.close()
        if conexion is not None and conexion.is_connected():
            conexion.close()


def obtener_gastos(rol):
    from datetime import date
    mes = date.today().month
    conexion = None
    cursor = None
    try:
        conexion = obtener_conexion(rol)
        cursor = conexion.cursor(dictionary=True)
        cursor.execute("""
            SELECT g.idGasto, g.descripcion, g.monto, g.fecha, m.nombre AS cuenta, m.num_cuenta
            FROM GASTO g
            JOIN METODO_DE_PAGO m ON g.idMetodo_de_pago = m.idMetodo_de_pago
            WHERE MONTH(g.fecha) = %s
            ORDER BY g.fecha DESC
        """, (mes,))
        return cursor.fetchall()
    except Error as e:
        raise Exception(f"Error al obtener gastos: {e}")
    finally:
        if cursor is not None: cursor.close()
        if conexion is not None and conexion.is_connected(): conexion.close()


def insertar_gasto(id_metodo_pago, descripcion, monto, rol):
    conexion = None
    cursor = None
    try:
        conexion = obtener_conexion(rol)
        cursor = conexion.cursor()
        
        # 1. Restar del saldo de la cuenta
        cursor.execute(
            "UPDATE METODO_DE_PAGO SET saldo = saldo - %s WHERE idMetodo_de_pago = %s",
            (monto, id_metodo_pago)
        )
        
        # 2. Insertar el registro del gasto
        cursor.execute(
            "INSERT INTO GASTO (idMetodo_de_pago, descripcion, monto) VALUES (%s, %s, %s)",
            (id_metodo_pago, descripcion, monto)
        )
        
        conexion.commit()
    except Error as e:
        if conexion:
            conexion.rollback()
        if e.errno == 3819 or "CONSTRAINT" in str(e).upper():
            raise Exception("Saldo insuficiente en la cuenta para registrar este gasto.")
        raise Exception(f"Error al registrar gasto: {e}")
    finally:
        if cursor is not None: cursor.close()
        if conexion is not None and conexion.is_connected(): conexion.close()


def obtener_resumen_financiero_7dias(rol):
    from datetime import date, timedelta
    conexion = None
    cursor = None
    try:
        conexion = obtener_conexion(rol)
        cursor = conexion.cursor(dictionary=True)

        hoy = date.today()
        hace_7 = hoy - timedelta(days=6)

        # 1. Saldo ACTUAL total (sumamos todos los métodos de pago)
        cursor.execute("SELECT COALESCE(SUM(saldo), 0) AS saldo_actual FROM METODO_DE_PAGO")
        saldo_actual = float(cursor.fetchone()['saldo_actual'])

        # 2. Gastos por día (últimos 7 días)
        cursor.execute("""
            SELECT DATE(fecha) AS dia, COALESCE(SUM(monto), 0) AS total
            FROM GASTO
            WHERE DATE(fecha) BETWEEN %s AND %s
            GROUP BY DATE(fecha)
        """, (hace_7, hoy))
        gastos_map = {str(r['dia']): float(r['total']) for r in cursor.fetchall()}

        # 3. Costos por día = envíos pagados + pagos de nómina + compras  
        cursor.execute("""
            SELECT DATE(fecha) AS dia, COALESCE(SUM(valor), 0) AS total
            FROM ENVIO
            WHERE DATE(fecha) BETWEEN %s AND %s
            GROUP BY DATE(fecha)
        """, (hace_7, hoy))
        envios_map = {str(r['dia']): float(r['total']) for r in cursor.fetchall()}

        cursor.execute("""
            SELECT DATE(fecha_pago) AS dia, COALESCE(SUM(monto), 0) AS total
            FROM PAGO_EMPLEADO
            WHERE DATE(fecha_pago) BETWEEN %s AND %s
            GROUP BY DATE(fecha_pago)
        """, (hace_7, hoy))
        nomina_map = {str(r['dia']): float(r['total']) for r in cursor.fetchall()}

        cursor.execute("""
            SELECT DATE(fechacompra) AS dia, COALESCE(SUM(total), 0) AS total
            FROM COMPRA
            WHERE DATE(fechacompra) BETWEEN %s AND %s
            GROUP BY DATE(fechacompra)
        """, (hace_7, hoy))
        compras_map = {str(r['dia']): float(r['total']) for r in cursor.fetchall()}

        # 4. CxC por día: ventas PENDIENTE hechas ese día
        cursor.execute("""
            SELECT DATE(fecha_venta) AS dia, COALESCE(SUM(valor_total), 0) AS total
            FROM VENTA
            WHERE estado_pago = 'PENDIENTE'
              AND DATE(fecha_venta) BETWEEN %s AND %s
            GROUP BY DATE(fecha_venta)
        """, (hace_7, hoy))
        cxc_map = {str(r['dia']): float(r['total']) for r in cursor.fetchall()}

        # 5. Abonos por día: pagos recibidos de clientes
        cursor.execute("""
            SELECT DATE(fecha_pago) AS dia, COALESCE(SUM(monto), 0) AS total
            FROM PAGO
            WHERE DATE(fecha_pago) BETWEEN %s AND %s
            GROUP BY DATE(fecha_pago)
        """, (hace_7, hoy))
        abonos_map = {str(r['dia']): float(r['total']) for r in cursor.fetchall()}

        # 6. Ventas totales por día (todas, sin importar estado de pago)
        cursor.execute("""
            SELECT DATE(fecha_venta) AS dia, COALESCE(SUM(valor_total), 0) AS total
            FROM VENTA
            WHERE DATE(fecha_venta) BETWEEN %s AND %s
            GROUP BY DATE(fecha_venta)
        """, (hace_7, hoy))
        ventas_map = {str(r['dia']): float(r['total']) for r in cursor.fetchall()}

        dias = []
        for i in range(7):
            d = hace_7 + timedelta(days=i)
            dias.append(str(d))

        # Calcular saldo_fin de cada día, empezando por hoy
        saldo_fin = {}
        saldo_fin[dias[6]] = saldo_actual  # hoy

        # De hoy hacia atrás
        for i in range(6, 0, -1):
            d = dias[i]
            g = gastos_map.get(d, 0)
            c = envios_map.get(d, 0) + nomina_map.get(d, 0) + compras_map.get(d, 0)
            a = abonos_map.get(d, 0)
            saldo_inicio_d = saldo_fin[d] + g + c - a
            saldo_fin[dias[i - 1]] = saldo_inicio_d

        # Armar resultado
        resultado = []
        for d in dias:
            g = gastos_map.get(d, 0)
            c = envios_map.get(d, 0) + nomina_map.get(d, 0) + compras_map.get(d, 0)
            a = abonos_map.get(d, 0)
            si = saldo_fin[d] + g + c - a
            resultado.append({
                'fecha': d,
                'saldo_inicial': si,
                'gastos': g,
                'costos': c,
                'cxc': cxc_map.get(d, 0),
                'abonos': a,
                'ventas_total': ventas_map.get(d, 0),
                'saldo_esperado': saldo_fin[d],
            })

        return resultado

    except Error as e:
        raise Exception(f"Error al obtener resumen financiero: {e}")
    finally:
        if cursor is not None: cursor.close()
        if conexion is not None and conexion.is_connected(): conexion.close()


def obtener_cuentas_por_cobrar(rol):
    conexion = None
    cursor = None
    try:
        conexion = obtener_conexion(rol)
        cursor = conexion.cursor(dictionary=True)
        consulta = """
            SELECT 
                v.idVenta, 
                v.fecha_venta, 
                c.nombre AS cliente,
                (SELECT COALESCE(SUM(dv.cantidad * prod.precio_venta), 0) 
                    FROM DETALLE_VENTA dv 
                    JOIN PRODUCTO prod ON dv.idProducto = prod.idProducto 
                    WHERE dv.idVenta = v.idVenta) AS total_productos,
                (SELECT COALESCE(SUM(p.monto), 0) 
                    FROM PAGO p 
                    WHERE p.idVenta = v.idVenta) AS total_abonado,
                ((SELECT COALESCE(SUM(dv.cantidad * prod.precio_venta), 0) 
                    FROM DETALLE_VENTA dv 
                    JOIN PRODUCTO prod ON dv.idProducto = prod.idProducto 
                    WHERE dv.idVenta = v.idVenta) 
                - 
                (SELECT COALESCE(SUM(p.monto), 0) 
                    FROM PAGO p 
                    WHERE p.idVenta = v.idVenta)) AS saldo_pendiente
            FROM VENTA v
            JOIN CLIENTE c ON v.idCliente = c.idCliente
            WHERE v.estado_pago = 'PENDIENTE'
            ORDER BY v.fecha_venta DESC
        """
        cursor.execute(consulta)
        return cursor.fetchall()
    except Error as e:
        raise Exception(f"Error al obtener cuentas por pagar: {e}")
    finally:
        if cursor is not None: cursor.close()
        if conexion is not None and conexion.is_connected(): conexion.close()
