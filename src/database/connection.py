import mysql.connector
from mysql.connector import Error

# ---------------------------------------------------------------------------
# CONFIGURACIÓN DE ACCESO A LA BASE DE DATOS POR ROL
# ---------------------------------------------------------------------------
# Se definen dos usuarios SQL con privilegios diferenciados (ver Usuarios.sql).
# NUNCA se usa 'root' para las operaciones de la aplicación.
#
#   rol = 1  →  Gerente  → usuario SQL: 'gerente'  (CRUD completo)
#   rol = 0  →  Empleado → usuario SQL: 'empleado' (permisos restringidos)
# ---------------------------------------------------------------------------

_HOST = 'localhost'
_PORT = 3306
_DATABASE = 'bd_tienda'

# Credenciales para validar el login (acceso mínimo: solo lectura de EMPLEADO)
# Se utiliza el usuario raíz ÚNICAMENTE en esta consulta inicial de autenticación.
# Una alternativa más segura sería un usuario de solo lectura sobre EMPLEADO.
_CONFIG_AUTH = {
    'host': _HOST,
    'user': 'log',
    'password': '123456',
    'database': _DATABASE,
    'port': _PORT
}

# Configuración para el usuario con rol Gerente
_CONFIG_GERENTE = {
    'host': _HOST,
    'user': 'gerente',
    'password': '0315',
    'database': _DATABASE,
    'port': _PORT
}

# Configuración para el usuario con rol Empleado común
_CONFIG_EMPLEADO = {
    'host': _HOST,
    'user': 'empleado',
    'password': '2709',
    'database': _DATABASE,
    'port': _PORT
}


def _config_por_rol(rol):
    """
    Retorna el diccionario de configuración de conexión correspondiente al rol.
    
    Parámetros:
        rol (int | bool): 1 para gerente, 0 para empleado común.
    """
    return _CONFIG_GERENTE if rol else _CONFIG_EMPLEADO


def obtener_conexion(rol=None):
    """
    Establece una conexión con la base de datos MySQL usando las credenciales
    del usuario SQL asociado al rol del empleado autenticado.

    Parámetros:
        rol (int | None): 
            - None  → usa el usuario de autenticación (solo para validar_credenciales)
            - 1     → conecta como 'gerente'
            - 0     → conecta como 'empleado'

    Retorna:
        conexion: objeto de conexión activo.
    Lanza:
        Exception: si la conexión falla.
    """
    config = _CONFIG_AUTH if rol is None else _config_por_rol(rol)
    try:
        conexion = mysql.connector.connect(**config)
        if conexion.is_connected():
            return conexion
    except Error as e:
        raise Exception(f"Error al conectar a la base de datos: {e}")

def validar_credenciales(usuario, contrasena):
    """
    Valida si un empleado existe en la base de datos usando su correo o documento como
    identificador de usuario, y su documento como contraseña.

    Ahora también retorna el campo 'rol' (BIT: 1=gerente, 0=empleado) para que la
    aplicación pueda conectarse a MySQL con el usuario SQL de menor privilegio necesario.
    
    Retorna:
        dict: Con los datos del empleado (idEmpleado, nombre, correo, rol) si las
              credenciales son correctas.
        None: Si las credenciales no son válidas.
    Lanza:
        Exception: Si ocurre un problema con la base de datos.
    """
    conexion = None
    cursor = None
    try:
        # 1. Conexión de autenticación (acceso temporal solo para verificar credenciales)
        conexion = obtener_conexion()  # rol=None → usa _CONFIG_AUTH
        
        # 2. Cursor con resultados como diccionario
        cursor = conexion.cursor(dictionary=True)
        
        # 3. Consulta parametrizada (previene Inyección SQL)
        # Se incluye el campo 'rol' para determinar qué usuario SQL debe usarse
        # en el resto de la sesión.
        consulta = """
            SELECT idEmpleado, nombre, documento, correo, rol 
            FROM EMPLEADO 
            WHERE (correo = %s OR documento = %s) 
              AND documento = %s
        """
        
        # 4. Ejecutar con valores seguros
        valores = (usuario, usuario, contrasena)
        cursor.execute(consulta, valores)
        
        # 5. Obtener el primer resultado (None si no hay coincidencia)
        empleado = cursor.fetchone()

        # 6. Normalizar el campo 'rol': MySQL retorna BIT como bytes (b'\x01' / b'\x00')
        #    Lo convertimos a int (1 o 0) para usarlo fácilmente en Python.
        if empleado and empleado.get('rol') is not None:
            empleado['rol'] = int.from_bytes(empleado['rol'], byteorder='big') if isinstance(empleado['rol'], (bytes, bytearray)) else int(empleado['rol'])
        
        return empleado

    except Error as e:
        raise Exception(f"Error de base de datos: {e}")
        
    finally:
        # 7. Limpieza: siempre cerrar cursor y conexión para liberar recursos
        if cursor is not None:
            cursor.close()
        if conexion is not None and conexion.is_connected():
            conexion.close()

def obtener_clientes(rol):
    """
    Obtiene todos los clientes de la base de datos.

    Parámetros:
        rol (int): Rol del empleado autenticado (1=gerente, 0=empleado).
                   Determina con qué usuario SQL se realiza la consulta.
    Retorna:
        list[dict]: Lista de clientes.
    """
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
    """
    Inserta un nuevo cliente en la base de datos.
    Mapea cadenas vacías a None para que queden guardadas como NULL en MySQL.

    Parámetros:
        rol (int): Rol del empleado autenticado (1=gerente, 0=empleado).
    Retorna:
        int: El idCliente autogenerado si fue exitoso.
    """
    # Limpieza de valores vacíos para campos opcionales
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
    """
    Actualiza la información de un cliente existente.

    Parámetros:
        rol (int): Rol del empleado autenticado (1=gerente, 0=empleado).
    """
    # Limpieza de valores vacíos para campos opcionales
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

def obtener_productos(rol):
    """
    Obtiene todos los productos de la base de datos.

    Parámetros:
        rol (int): Rol del empleado autenticado (1=gerente, 0=empleado).
    Retorna:
        list[dict]: Lista de productos.
    """
    conexion = None
    cursor = None
    try:
        conexion = obtener_conexion(rol)
        cursor = conexion.cursor(dictionary=True)
        cursor.execute("SELECT idProducto, nombre, referencia, precio_venta, bodega, descripcion FROM PRODUCTO")
        productos = cursor.fetchall()
        return productos
    except Error as e:
        raise Exception(f"Error al obtener productos: {e}")
    finally:
        if cursor is not None:
            cursor.close()
        if conexion is not None and conexion.is_connected():
            conexion.close()

def obtener_saldos_cuentas(rol):
    """
    Obtiene los métodos de pago (cuentas) y el saldo total de cada una
    basado en los pagos registrados.

    Parámetros:
        rol (int): Rol del empleado autenticado (1=gerente, 0=empleado).
    Retorna:
        list[dict]: Lista de cuentas con saldo acumulado.
    """
    conexion = None
    cursor = None
    try:
        conexion = obtener_conexion(rol)
        cursor = conexion.cursor(dictionary=True)
        consulta = """
            SELECT 
                m.idMetodo_de_pago,
                m.nombre AS tipo_cuenta, 
                m.num_cuenta, 
                COALESCE(SUM(p.monto), 0) AS saldo_total
            FROM METODO_DE_PAGO m
            LEFT JOIN PAGO p ON m.idMetodo_de_pago = p.idMetodo_de_pago
            GROUP BY m.idMetodo_de_pago, m.nombre, m.num_cuenta
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
