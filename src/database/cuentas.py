from datetime import date
from database.base import db_cursor, _convertir_filas, SmartDict


def obtener_saldos_cuentas(rol=None):
    """Obtiene los saldos actuales de todas las cuentas y métodos de pago."""
    try:
        with db_cursor(commit=False, dictionary=True) as (cursor, _):
            consulta = """
                SELECT 
                    idMetodo_de_pago,
                    nombre AS tipo_cuenta, 
                    num_cuenta, 
                    saldo AS saldo_total
                FROM METODO_DE_PAGO
                ORDER BY idMetodo_de_pago
            """
            cursor.execute(consulta)
            cuentas = cursor.fetchall()
            return _convertir_filas(cuentas) or []
    except Exception as e:
        raise Exception(f"Error al obtener saldos de cuentas: {e}")


def obtener_gastos(rol=None):
    """Obtiene los gastos del mes actual con la cuenta de procedencia."""
    hoy = date.today()
    try:
        with db_cursor(commit=False, dictionary=True) as (cursor, _):
            cursor.execute("""
                SELECT g.idGasto, g.descripcion, g.monto, g.fecha, m.nombre AS cuenta, m.num_cuenta
                FROM GASTO g
                JOIN METODO_DE_PAGO m ON g.idMetodo_de_pago = m.idMetodo_de_pago
                WHERE EXTRACT(MONTH FROM g.fecha) = %s AND EXTRACT(YEAR FROM g.fecha) = %s
                ORDER BY g.fecha DESC
            """, (hoy.month, hoy.year))
            gastos = cursor.fetchall()
            return _convertir_filas(gastos) or []
    except Exception as e:
        raise Exception(f"Error al obtener gastos: {e}")


def insertar_gasto(id_metodo_pago, descripcion, monto, rol=None):
    """Registra un nuevo gasto descontando del saldo de la cuenta indicada."""
    monto = float(monto)
    if monto <= 0:
        raise Exception("El monto del gasto debe ser mayor a cero.")
    descripcion = descripcion.strip()

    try:
        with db_cursor(commit=True, dictionary=True) as (cursor, _):
            # 1. Descontar saldo
            cursor.execute(
                "UPDATE METODO_DE_PAGO SET saldo = saldo - %s WHERE idMetodo_de_pago = %s",
                (monto, id_metodo_pago)
            )
            # 2. Registrar gasto
            cursor.execute(
                "INSERT INTO GASTO (idMetodo_de_pago, descripcion, monto) VALUES (%s, %s, %s)",
                (id_metodo_pago, descripcion, monto)
            )
    except Exception as e:
        err_msg = str(e).lower()
        if "check" in err_msg or "violates" in err_msg or "saldo" in err_msg:
            raise Exception("Saldo insuficiente en la cuenta para registrar este gasto.")
        raise Exception(f"Error al registrar gasto: {e}")


def obtener_resumen_financiero_7dias(rol=None):
    """
    Obtiene el resumen financiero de los últimos 7 días en UNA SOLA consulta consolidada
    a Supabase, eliminando latencia de peticiones múltiples y calculando saldos históricos.
    """
    try:
        with db_cursor(commit=False, dictionary=True) as (cursor, _):
            consulta = """
                WITH 
                dias AS (
                    SELECT (CURRENT_DATE - (i || ' day')::interval)::date AS dia
                    FROM generate_series(6, 0, -1) AS i
                ),
                tot_saldo AS (
                    SELECT COALESCE(SUM(saldo), 0) AS saldo_actual FROM METODO_DE_PAGO
                ),
                gastos_agg AS (
                    SELECT fecha::date AS dia, SUM(monto) AS total
                    FROM GASTO
                    WHERE fecha::date >= CURRENT_DATE - 6 AND fecha::date <= CURRENT_DATE
                    GROUP BY fecha::date
                ),
                envios_agg AS (
                    SELECT fecha AS dia, SUM(valor) AS total
                    FROM ENVIO
                    WHERE fecha >= CURRENT_DATE - 6 AND fecha <= CURRENT_DATE
                    GROUP BY fecha
                ),
                nomina_agg AS (
                    SELECT fecha_pago::date AS dia, SUM(monto) AS total
                    FROM PAGO_EMPLEADO
                    WHERE fecha_pago::date >= CURRENT_DATE - 6 AND fecha_pago::date <= CURRENT_DATE
                    GROUP BY fecha_pago::date
                ),
                compras_agg AS (
                    SELECT fechacompra::date AS dia, SUM(total) AS total
                    FROM COMPRA
                    WHERE fechacompra::date >= CURRENT_DATE - 6 AND fechacompra::date <= CURRENT_DATE
                    GROUP BY fechacompra::date
                ),
                cxc_agg AS (
                    SELECT fecha_venta::date AS dia, SUM(valor_total) AS total
                    FROM VENTA
                    WHERE estado_pago = 'PENDIENTE' 
                      AND fecha_venta::date >= CURRENT_DATE - 6 
                      AND fecha_venta::date <= CURRENT_DATE
                    GROUP BY fecha_venta::date
                ),
                abonos_agg AS (
                    SELECT fecha_pago::date AS dia, SUM(monto) AS total
                    FROM PAGO
                    WHERE fecha_pago::date >= CURRENT_DATE - 6 
                      AND fecha_pago::date <= CURRENT_DATE
                    GROUP BY fecha_pago::date
                ),
                ventas_agg AS (
                    SELECT fecha_venta::date AS dia, SUM(valor_total) AS total
                    FROM VENTA
                    WHERE fecha_venta::date >= CURRENT_DATE - 6 
                      AND fecha_venta::date <= CURRENT_DATE
                    GROUP BY fecha_venta::date
                )
                SELECT 
                    d.dia,
                    (SELECT saldo_actual FROM tot_saldo) AS saldo_actual,
                    COALESCE(g.total, 0) AS gasto,
                    (COALESCE(e.total, 0) + COALESCE(n.total, 0) + COALESCE(c.total, 0)) AS costo,
                    COALESCE(cxc.total, 0) AS cxc,
                    COALESCE(a.total, 0) AS abono,
                    COALESCE(v.total, 0) AS venta_total
                FROM dias d
                LEFT JOIN gastos_agg g ON d.dia = g.dia
                LEFT JOIN envios_agg e ON d.dia = e.dia
                LEFT JOIN nomina_agg n ON d.dia = n.dia
                LEFT JOIN compras_agg c ON d.dia = c.dia
                LEFT JOIN cxc_agg cxc ON d.dia = cxc.dia
                LEFT JOIN abonos_agg a ON d.dia = a.dia
                LEFT JOIN ventas_agg v ON d.dia = v.dia
                ORDER BY d.dia ASC;
            """
            cursor.execute(consulta)
            filas = cursor.fetchall()
            if not filas:
                return []

            filas_smart = _convertir_filas(filas)
            saldo_actual = float(filas_smart[-1].get('saldo_actual', 0))

            # Calcular saldo_fin de cada día de hoy hacia atrás
            n = len(filas_smart)
            saldo_fin = {}
            if n > 0:
                saldo_fin[n - 1] = saldo_actual
                for i in range(n - 1, 0, -1):
                    row = filas_smart[i]
                    g = float(row.get('gasto', 0))
                    c = float(row.get('costo', 0))
                    a = float(row.get('abono', 0))
                    saldo_inicio = saldo_fin[i] + g + c - a
                    saldo_fin[i - 1] = saldo_inicio

            resultado = []
            for i, row in enumerate(filas_smart):
                d_str = str(row['dia'])
                g = float(row.get('gasto', 0))
                c = float(row.get('costo', 0))
                a = float(row.get('abono', 0))
                si = saldo_fin.get(i, 0) + g + c - a
                resultado.append({
                    'fecha': d_str,
                    'saldo_inicial': si,
                    'gastos': g,
                    'costos': c,
                    'cxc': float(row.get('cxc', 0)),
                    'abonos': a,
                    'ventas_total': float(row.get('venta_total', 0)),
                    'saldo_esperado': saldo_fin.get(i, 0),
                })

            return resultado
    except Exception as e:
        raise Exception(f"Error al obtener resumen financiero: {e}")


def obtener_cuentas_por_cobrar(rol=None):
    """
    Obtiene todas las cuentas por cobrar (ventas a crédito pendientes)
    con su total calculado y saldo pendiente en una sola consulta optimizada.
    """
    try:
        with db_cursor(commit=False, dictionary=True) as (cursor, _):
            consulta = """
                SELECT 
                    v.idVenta, 
                    v.fecha_venta, 
                    c.nombre AS cliente,
                    v.valor_total AS total_productos,
                    COALESCE(SUM(p.monto), 0) AS total_abonado,
                    (v.valor_total - COALESCE(SUM(p.monto), 0)) AS saldo_pendiente
                FROM VENTA v
                JOIN CLIENTE c ON v.idCliente = c.idCliente
                LEFT JOIN PAGO p ON v.idVenta = p.idVenta
                WHERE v.estado_pago = 'PENDIENTE'
                GROUP BY v.idVenta, v.fecha_venta, c.nombre, v.valor_total
                ORDER BY v.fecha_venta DESC
            """
            cursor.execute(consulta)
            cuentas = cursor.fetchall()
            return _convertir_filas(cuentas) or []
    except Exception as e:
        raise Exception(f"Error al obtener cuentas por cobrar: {e}")
