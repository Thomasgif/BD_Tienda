import psycopg2
from database.base import db_cursor, _convertir_filas, SmartDict


def obtener_empleados(rol=None):
    """Obtiene el listado completo de empleados y sus roles."""
    try:
        with db_cursor(commit=False, dictionary=True) as (cursor, _):
            cursor.execute("""
                SELECT idEmpleado, nombre, documento,
                       trabajo_hora, pago_hora, telefono, correo, rol
                FROM EMPLEADO
                ORDER BY nombre
            """)
            empleados = cursor.fetchall()
            empleados_smart = _convertir_filas(empleados) or []
            for emp in empleados_smart:
                emp['rol'] = int(emp.get('rol', 0) or 0)
            return empleados_smart
    except Exception as e:
        raise Exception(f"Error al obtener empleados: {e}")


def obtener_ventas_mes_empleado(id_empleado, rol=None):
    """Obtiene las ventas realizadas por un empleado en el mes corriente."""
    try:
        with db_cursor(commit=False, dictionary=True) as (cursor, _):
            consulta = """
                SELECT idVenta, fecha_venta, valor_total, estado_pago
                FROM VENTA
                WHERE idEmpleado = %s
                  AND EXTRACT(MONTH FROM fecha_venta) = EXTRACT(MONTH FROM CURRENT_DATE)
                  AND EXTRACT(YEAR FROM fecha_venta)  = EXTRACT(YEAR FROM CURRENT_DATE)
                ORDER BY fecha_venta DESC
            """
            cursor.execute(consulta, (id_empleado,))
            ventas = cursor.fetchall()
            return _convertir_filas(ventas) or []
    except Exception as e:
        raise Exception(f"Error al obtener ventas del empleado: {e}")


def pagar_empleado(id_empleado, id_metodo_pago, monto, rol=None):
    """Procesa el pago de nómina de un empleado y reinicia sus horas acumuladas."""
    monto = float(monto)
    try:
        with db_cursor(commit=True, dictionary=True) as (cursor, _):
            # 1. Restar del saldo de la cuenta de la empresa
            cursor.execute(
                "UPDATE METODO_DE_PAGO SET saldo = saldo - %s WHERE idMetodo_de_pago = %s",
                (monto, id_metodo_pago)
            )

            # 2. Registrar el pago
            cursor.execute(
                "INSERT INTO PAGO_EMPLEADO (idEmpleado, idMetodo_de_pago, monto) VALUES (%s, %s, %s)",
                (id_empleado, id_metodo_pago, monto)
            )

            # 3. Reiniciar horas trabajadas
            cursor.execute(
                "UPDATE EMPLEADO SET trabajo_hora = 0 WHERE idEmpleado = %s",
                (id_empleado,)
            )
    except Exception as e:
        err_msg = str(e).lower()
        if "check" in err_msg or "violates" in err_msg or "saldo" in err_msg:
            raise Exception("Saldo insuficiente en la cuenta para realizar el pago de nómina.")
        raise Exception(f"Error al procesar pago de empleado: {e}")


def insertar_empleado(nombre, documento, trabajo_hora, pago_hora, telefono, correo, rol_empleado, rol=None):
    """Registra un nuevo empleado en Supabase."""
    nombre = nombre.strip()
    documento = documento.strip()
    telefono = telefono.strip() if telefono and telefono.strip() else None
    correo = correo.strip() if correo and correo.strip() else None

    try:
        with db_cursor(commit=True, dictionary=True) as (cursor, _):
            consulta = """
                INSERT INTO EMPLEADO (nombre, documento, trabajo_hora, pago_hora, telefono, correo, rol)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING idEmpleado
            """
            cursor.execute(consulta, (nombre, documento, trabajo_hora, pago_hora, telefono, correo, rol_empleado))
            nuevo = cursor.fetchone()
            return nuevo['idempleado'] if nuevo and 'idempleado' in nuevo else (nuevo['idEmpleado'] if nuevo else None)
    except psycopg2.IntegrityError as e:
        if "unique" in str(e).lower() or "documento" in str(e).lower():
            raise Exception("El documento ingresado ya está registrado para otro empleado.")
        raise Exception(f"Error al registrar empleado: {e}")
    except Exception as e:
        if "unique" in str(e).lower() or "documento" in str(e).lower():
            raise Exception("El documento ingresado ya está registrado para otro empleado.")
        raise Exception(f"Error al registrar empleado: {e}")


def actualizar_empleado(id_empleado, nombre, documento, trabajo_hora, pago_hora, telefono, correo, rol_empleado, rol=None):
    """Actualiza los datos y salario de un empleado existente."""
    nombre = nombre.strip()
    documento = documento.strip()
    telefono = telefono.strip() if telefono and telefono.strip() else None
    correo = correo.strip() if correo and correo.strip() else None

    try:
        with db_cursor(commit=True, dictionary=True) as (cursor, _):
            consulta = """
                UPDATE EMPLEADO
                SET nombre = %s, documento = %s, trabajo_hora = %s, pago_hora = %s, telefono = %s, correo = %s, rol = %s
                WHERE idEmpleado = %s
            """
            cursor.execute(consulta, (nombre, documento, trabajo_hora, pago_hora, telefono, correo, rol_empleado, id_empleado))
    except psycopg2.IntegrityError as e:
        if "unique" in str(e).lower() or "documento" in str(e).lower():
            raise Exception("El documento ingresado ya está registrado para otro empleado.")
        raise Exception(f"Error al actualizar empleado: {e}")
    except Exception as e:
        if "unique" in str(e).lower() or "documento" in str(e).lower():
            raise Exception("El documento ingresado ya está registrado para otro empleado.")
        raise Exception(f"Error al actualizar empleado: {e}")


def eliminar_empleado(id_empleado, rol=None):
    """Elimina un empleado de la base de datos si no tiene registros históricos."""
    try:
        with db_cursor(commit=True, dictionary=True) as (cursor, _):
            cursor.execute("DELETE FROM EMPLEADO WHERE idEmpleado = %s", (id_empleado,))
    except psycopg2.IntegrityError as e:
        raise Exception("No se puede eliminar el empleado porque tiene registros asociados (ventas, compras, etc.).")
    except Exception as e:
        if "violates foreign key" in str(e).lower():
            raise Exception("No se puede eliminar el empleado porque tiene registros asociados (ventas, compras, etc.).")
        raise Exception(f"Error al eliminar empleado: {e}")
