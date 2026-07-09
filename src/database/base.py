import mysql.connector
from mysql.connector import Error

_HOST = 'localhost'
_PORT = 3306
_DATABASE = 'bd_tienda'

_CONFIG_AUTH = {
    'host': _HOST,
    'user': 'log',
    'password': '123456',
    'database': _DATABASE,
    'port': _PORT
}

_CONFIG_GERENTE = {
    'host': _HOST,
    'user': 'gerente',
    'password': '0315',
    'database': _DATABASE,
    'port': _PORT
}

_CONFIG_EMPLEADO = {
    'host': _HOST,
    'user': 'empleado',
    'password': '2709',
    'database': _DATABASE,
    'port': _PORT
}


def _config_por_rol(rol):
    return _CONFIG_GERENTE if rol else _CONFIG_EMPLEADO


def obtener_conexion(rol=None):
    config = _CONFIG_AUTH if rol is None else _config_por_rol(rol)
    try:
        conexion = mysql.connector.connect(**config)
        if conexion.is_connected():
            return conexion
    except Error as e:
        raise Exception(f"Error al conectar a la base de datos: {e}")


def validar_credenciales(usuario, contrasena):
    conexion = None
    cursor = None
    try:
        conexion = obtener_conexion()
        cursor = conexion.cursor(dictionary=True)
        consulta = """
            SELECT idEmpleado, nombre, documento, correo, rol 
            FROM EMPLEADO 
            WHERE (correo = %s OR documento = %s) 
              AND documento = %s
        """
        valores = (usuario, usuario, contrasena)
        cursor.execute(consulta, valores)
        empleado = cursor.fetchone()
        if empleado and empleado.get('rol') is not None:
            empleado['rol'] = int.from_bytes(empleado['rol'], byteorder='big') if isinstance(empleado['rol'], (bytes, bytearray)) else int(empleado['rol'])
        return empleado
    except Error as e:
        raise Exception(f"Error de base de datos: {e}")
    finally:
        if cursor is not None:
            cursor.close()
        if conexion is not None and conexion.is_connected():
            conexion.close()
