from mysql.connector import Error
from database.base import obtener_conexion


def obtener_clientes(rol):
    conexion = None
    cursor = None
    try:
        conexion = obtener_conexion(rol)
        cursor = conexion.cursor(dictionary=True)
        cursor.execute("SELECT idCliente, nombre, apellidos, documento, telefono, correo, direccion FROM CLIENTE")
        clientes = cursor.fetchall()
        return clientes
    except Error as e:
        raise Exception(f"Error al obtener clientes: {e}")
    finally:
        if cursor is not None:
            cursor.close()
        if conexion is not None and conexion.is_connected():
            conexion.close()


def insertar_cliente(nombre, apellidos, documento, rol, telefono=None, correo=None, direccion=None):
    telefono = telefono.strip() if telefono and telefono.strip() else None
    correo = correo.strip() if correo and correo.strip() else None
    direccion = direccion.strip() if direccion and direccion.strip() else None
    
    nombre = nombre.strip()
    apellidos = apellidos.strip()
    documento = documento.strip()

    conexion = None
    cursor = None
    try:
        conexion = obtener_conexion(rol)
        cursor = conexion.cursor()
        
        consulta = """
            INSERT INTO CLIENTE (nombre, apellidos, documento, telefono, correo, direccion)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        valores = (nombre, apellidos, documento, telefono, correo, direccion)
        cursor.execute(consulta, valores)
        conexion.commit()
        
        return cursor.lastrowid
    except Error as e:
        if e.errno == 1062:
            raise Exception("El documento ingresado ya está registrado para otro cliente.")
        raise Exception(f"Error al registrar cliente en la base de datos: {e}")
    finally:
        if cursor is not None:
            cursor.close()
        if conexion is not None and conexion.is_connected():
            conexion.close()


def actualizar_cliente(id_cliente, nombre, apellidos, documento, rol, telefono=None, correo=None, direccion=None):
    telefono = telefono.strip() if telefono and telefono.strip() else None
    correo = correo.strip() if correo and correo.strip() else None
    direccion = direccion.strip() if direccion and direccion.strip() else None
    
    nombre = nombre.strip()
    apellidos = apellidos.strip()
    documento = documento.strip()

    conexion = None
    cursor = None
    try:
        conexion = obtener_conexion(rol)
        cursor = conexion.cursor()
        
        consulta = """
            UPDATE CLIENTE 
            SET nombre = %s, apellidos = %s, documento = %s, telefono = %s, correo = %s, direccion = %s
            WHERE idCliente = %s
        """
        valores = (nombre, apellidos, documento, telefono, correo, direccion, id_cliente)
        cursor.execute(consulta, valores)
        conexion.commit()
    except Error as e:
        if e.errno == 1062:
            raise Exception("El documento ingresado ya está registrado para otro cliente.")
        raise Exception(f"Error al actualizar cliente en la base de datos: {e}")
    finally:
        if cursor is not None:
            cursor.close()
        if conexion is not None and conexion.is_connected():
            conexion.close()


def obtener_deudas_cliente(idcli, rol):
    conexion = None
    cursor = None
    try:
        conexion = obtener_conexion(rol)
        cursor = conexion.cursor(dictionary=True)
        cursor.execute(
            "SELECT idVenta, fecha_venta, valor_total FROM VENTA WHERE idCliente = %s AND estado_pago='PENDIENTE'", (idcli,))
        deudas = cursor.fetchall()
        return deudas
    except Error as e:
        raise Exception(f"Error al obtener deudas del cliente: {e}")
    finally:
        if cursor is not None:
            cursor.close()
        if conexion is not None and conexion.is_connected():
            conexion.close()
