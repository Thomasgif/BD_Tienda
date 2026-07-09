from mysql.connector import Error
from database.base import obtener_conexion


def obtener_empleados(rol):
    conexion = None
    cursor = None
    try:
        conexion = obtener_conexion(rol)
        cursor = conexion.cursor(dictionary=True)
        cursor.execute("""
            SELECT idEmpleado, nombre, documento,
                   trabajo_hora, pago_hora, telefono, correo, rol
            FROM EMPLEADO
            ORDER BY nombre
        """)
        empleados = cursor.fetchall()
        # Normalizar campo BIT
        for emp in empleados:
            r = emp.get('rol', 0)
            emp['rol'] = int.from_bytes(r, 'big') if isinstance(r, (bytes, bytearray)) else int(r or 0)
        return empleados
    except Error as e:
        raise Exception(f"Error al obtener empleados: {e}")
    finally:
        if cursor is not None: cursor.close()
        if conexion is not None and conexion.is_connected(): conexion.close()


def obtener_ventas_mes_empleado(id_empleado, rol):
    conexion = None
    cursor = None
    try:
        conexion = obtener_conexion(rol)
        cursor = conexion.cursor(dictionary=True)
        consulta = """
            SELECT idVenta, fecha_venta, valor_total, estado_pago
            FROM VENTA
            WHERE idEmpleado = %s
              AND MONTH(fecha_venta) = MONTH(CURDATE())
              AND YEAR(fecha_venta)  = YEAR(CURDATE())
            ORDER BY fecha_venta DESC
        """
        cursor.execute(consulta, (id_empleado,))
        return cursor.fetchall()
    except Error as e:
        raise Exception(f"Error al obtener ventas del empleado: {e}")
    finally:
        if cursor is not None: cursor.close()
        if conexion is not None and conexion.is_connected(): conexion.close()


def pagar_empleado(id_empleado, id_metodo_pago, monto, rol):
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

        conexion.commit()
    except Error as e:
        if conexion:
            conexion.rollback()
        if e.errno == 3819 or "CONSTRAINT" in str(e).upper():
            raise Exception("Saldo insuficiente en la cuenta para realizar el pago de nómina.")
        raise Exception(f"Error al procesar pago de empleado: {e}")
    finally:
        if cursor is not None: cursor.close()
        if conexion is not None and conexion.is_connected(): conexion.close()


def insertar_empleado(nombre, documento, trabajo_hora, pago_hora, telefono, correo, rol_empleado, rol):
    conexion = None
    cursor = None
    try:
        conexion = obtener_conexion(rol)
        cursor = conexion.cursor()
        consulta = """
            INSERT INTO EMPLEADO (nombre, documento, trabajo_hora, pago_hora, telefono, correo, rol)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(consulta, (nombre, documento, trabajo_hora, pago_hora, telefono, correo, rol_empleado))
        conexion.commit()
    except Error as e:
        if e.errno == 1062:
            raise Exception("El documento ingresado ya está registrado para otro empleado.")
        raise Exception(f"Error al registrar empleado: {e}")
    finally:
        if cursor is not None: cursor.close()
        if conexion is not None and conexion.is_connected(): conexion.close()


def actualizar_empleado(id_empleado, nombre, documento, trabajo_hora, pago_hora, telefono, correo, rol_empleado, rol):
    conexion = None
    cursor = None
    try:
        conexion = obtener_conexion(rol)
        cursor = conexion.cursor()
        consulta = """
            UPDATE EMPLEADO
            SET nombre = %s, documento = %s, trabajo_hora = %s, pago_hora = %s, telefono = %s, correo = %s, rol = %s
            WHERE idEmpleado = %s
        """
        cursor.execute(consulta, (nombre, documento, trabajo_hora, pago_hora, telefono, correo, rol_empleado, id_empleado))
        conexion.commit()
    except Error as e:
        if e.errno == 1062:
            raise Exception("El documento ingresado ya está registrado para otro empleado.")
        raise Exception(f"Error al actualizar empleado: {e}")
    finally:
        if cursor is not None: cursor.close()
        if conexion is not None and conexion.is_connected(): conexion.close()


def eliminar_empleado(id_empleado, rol):
    conexion = None
    cursor = None
    try:
        conexion = obtener_conexion(rol)
        cursor = conexion.cursor()
        cursor.execute("DELETE FROM EMPLEADO WHERE idEmpleado = %s", (id_empleado,))
        conexion.commit()
    except Error as e:
        if e.errno == 1451:
            raise Exception("No se puede eliminar el empleado porque tiene registros asociados (ventas, compras, etc.).")
        raise Exception(f"Error al eliminar empleado: {e}")
    finally:
        if cursor is not None: cursor.close()
        if conexion is not None and conexion.is_connected(): conexion.close()
