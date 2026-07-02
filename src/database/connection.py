import mysql.connector
from mysql.connector import Error
from math import isfinite

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

def obtener_deudas_cliente(idcli, rol):
    """
    Obtiene las deudas pendientes de un cliente.
    """
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

def pago_total_venta(idventa, rol):
    """
    Obtiene el pago total de una venta.
    """
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
    """
    Registra un pago (total o parcial) para una venta PENDIENTE.
    - Inserta el registro en PAGO y actualiza el saldo del método de pago.
    - Si la suma de pagos >= valor_total de la venta, cambia estado a PAGADO.
    - Si es un pago parcial, la venta sigue en PENDIENTE.
    """
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
            "INSERT INTO PAGO (idCliente, idVenta, idMetodo_de_pago, monto) VALUES (%s, %s, %s, %s)",
            (id_cliente, id_venta, id_metodo_pago, monto)
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
    """
    Cancela una venta pendiente:
    - Cambia estado_pago a 'CANCELADO'
    - Restaura el inventario (bodega) de cada producto en DETALLE_VENTA
    Solo se puede cancelar ventas en estado PENDIENTE.
    """
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

        cursor.execute(
            "SELECT COALESCE(SUM(monto), 0) AS pagado FROM PAGO WHERE idVenta = %s",
            (id_venta,)
        )
        if float(cursor.fetchone()['pagado']) > 0:
            raise Exception(
                "No se puede cancelar una venta que ya tiene abonos. "
                "Primero debe gestionarse la devolución del dinero."
            )

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
    directamente desde la columna saldo.

    Parámetros:
        rol (int): Rol del empleado autenticado (1=gerente, 0=empleado).
    Retorna:
        list[dict]: Lista de cuentas con saldo.
    """
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

def obtener_proveedores(rol):
    conexion = None
    cursor = None
    try:
        conexion = obtener_conexion(rol)
        cursor = conexion.cursor(dictionary=True)
        cursor.execute("SELECT idProveedor, nombre, nit FROM PROVEEDOR")
        return cursor.fetchall()
    except Error as e:
        raise Exception(f"Error al obtener proveedores: {e}")
    finally:
        if cursor is not None: cursor.close()
        if conexion is not None and conexion.is_connected(): conexion.close()

def obtener_compras(rol):
    conexion = None
    cursor = None
    try:
        conexion = obtener_conexion(rol)
        cursor = conexion.cursor(dictionary=True)
        cursor.execute("SELECT idCompra, fechacompra, idProveedor FROM COMPRA")
        return cursor.fetchall()
    except Error as e:
        raise Exception(f"Error al obtener compras: {e}")
    finally:
        if cursor is not None: cursor.close()
        if conexion is not None and conexion.is_connected(): conexion.close()



def obtener_pedidos_proveedor(id_proveedor, rol):
    conexion = None
    cursor = None
    try:
        conexion = obtener_conexion(rol)
        cursor = conexion.cursor(dictionary=True)
        consulta = """
            SELECT c.idCompra, c.fechacompra, e.idEnvio, e.fecha AS fecha_envio, COALESCE(e.valor, 0) as valor
            FROM COMPRA c
            LEFT JOIN ENVIO e ON c.idCompra = e.idCompra
            WHERE c.idProveedor = %s
        """
        cursor.execute(consulta, (id_proveedor,))
        return cursor.fetchall()
    except Exception as e:
        raise Exception(f"Error al obtener pedidos del proveedor: {e}")
    finally:
        if cursor is not None: cursor.close()
        if conexion is not None and conexion.is_connected(): conexion.close()



def obtener_envios_list(rol):
    conexion = None
    cursor = None
    try:
        conexion = obtener_conexion(rol)
        cursor = conexion.cursor(dictionary=True)
        consulta = """
            SELECT e.idEnvio, e.idCompra, e.fecha, e.valor, p.nombre AS proveedor,
                   e.idMetodo_de_pago, m.nombre AS metodo_pago, m.num_cuenta
            FROM ENVIO e
            JOIN COMPRA c ON e.idCompra = c.idCompra
            JOIN PROVEEDOR p ON c.idProveedor = p.idProveedor
            LEFT JOIN METODO_DE_PAGO m ON e.idMetodo_de_pago = m.idMetodo_de_pago
            ORDER BY e.fecha DESC
        """
        cursor.execute(consulta)
        return cursor.fetchall()
    except Exception as e:
        raise Exception(f"Error al obtener envíos: {e}")
    finally:
        if cursor is not None: cursor.close()
        if conexion is not None and conexion.is_connected(): conexion.close()


def insertar_envio(idCompra, idEmpleado, fecha, valor, idMetodo_de_pago, rol):
    conexion = None
    cursor = None
    try:
        conexion = obtener_conexion(rol)
        cursor = conexion.cursor()
        
        # Restar del saldo de la cuenta
        cursor.execute(
            "UPDATE METODO_DE_PAGO SET saldo = saldo - %s WHERE idMetodo_de_pago = %s",
            (valor, idMetodo_de_pago)
        )
        
        consulta = "INSERT INTO ENVIO (idCompra, idEmpleado, fecha, valor, idMetodo_de_pago) VALUES (%s, %s, %s, %s, %s)"
        cursor.execute(consulta, (idCompra, idEmpleado, fecha, valor, idMetodo_de_pago))
        conexion.commit()
    except Error as e:
        if conexion:
            conexion.rollback()
        if e.errno == 3819 or "CONSTRAINT" in str(e).upper():
            raise Exception("Saldo insuficiente en la cuenta para realizar el envío.")
        raise Exception(f"Error al registrar el envío: {e}")
    except Exception as e:
        if conexion:
            conexion.rollback()
        raise e
    finally:
        if cursor is not None: cursor.close()
        if conexion is not None and conexion.is_connected(): conexion.close()

def obtener_detalle_compra(idCompra, rol):
    conexion = None
    cursor = None
    try:
        conexion = obtener_conexion(rol)
        cursor = conexion.cursor(dictionary=True)
        consulta = """
            SELECT p.nombre, p.referencia, d.cantidad, p.precio_compra, (d.cantidad * p.precio_compra) as subtotal
            FROM DETALLE_COMPRA d
            JOIN PRODUCTO p ON d.idProducto = p.idProducto
            WHERE d.idCompra = %s
        """
        cursor.execute(consulta, (idCompra,))
        return cursor.fetchall()
    except Exception as e:
        raise Exception(f"Error al obtener detalle de compra: {e}")
    finally:
        if cursor is not None: cursor.close()
        if conexion is not None and conexion.is_connected(): conexion.close()

# ---------------------------------------------------------------------------
# MÓDULO GERENTE — NÓMINA DE EMPLEADOS
# ---------------------------------------------------------------------------

def obtener_empleados(rol):
    """
    Obtiene todos los empleados con sus datos de nómina.
    Normaliza el campo 'rol' (BIT) a int (1=gerente, 0=empleado).

    Retorna:
        list[dict]: idEmpleado, nombre, documento, trabajo_hora,
                    pago_hora, telefono, correo, rol (int).
    """
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
    """
    Obtiene las ventas del mes y año actuales de un empleado específico.

    Retorna:
        list[dict]: idVenta, fecha_venta, valor_total, estado_pago.
    """
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
    """
    Procesa el pago de nómina de un empleado en una transacción atómica:
      1. Resta el saldo del método de pago de la empresa.
      2. Inserta un registro en PAGO_EMPLEADO.
      3. Resetea trabajo_hora = 0 en EMPLEADO.

    Parámetros:
        id_empleado   (int): ID del empleado a pagar.
        id_metodo_pago (int): Cuenta empresa de la que sale el dinero.
        monto         (float): Total a pagar (pago_hora × trabajo_hora).
        rol           (int): Rol SQL activo (debe ser 1=gerente).
    """
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


# ---------------------------------------------------------------------------
# MÓDULO GERENTE — CRUD DE EMPLEADOS
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# MÓDULO GERENTE — BALANCE & GASTOS & CUENTAS POR PAGAR
# ---------------------------------------------------------------------------

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
    """
    Obtiene un resumen financiero diario de los últimos 7 días.

    Para cada día retorna:
        - fecha:         la fecha del día
        - saldo_inicial: saldo al inicio del día (antes de movimientos)
        - gastos:        suma de GASTO.monto del día
        - costos:        suma de ENVIO.valor (compras+envíos pagados) + PAGO_EMPLEADO.monto del día
        - cxc:           valor_total de ventas PENDIENTE hechas ese día
        - abonos:        suma de PAGO.monto (pagos recibidos de clientes) del día
        - ventas_total:  valor_total de TODAS las ventas del día
        - saldo_esperado: saldo_inicial - gastos - costos + abonos

    Retorna:
        list[dict]: Una fila por día, ordenada del más antiguo al más reciente.
    """
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

        # 7. Reconstruir saldo_inicial de cada día
        # El saldo actual refleja TODOS los movimientos hasta hoy.
        # Recorremos de hoy hacia atrás, deshaciendo movimientos:
        #   saldo_inicio(dia) = saldo_fin(dia) + gastos(dia) + costos(dia) - abonos(dia)
        #   saldo_fin(dia) = saldo_inicio(dia+1)  ;  saldo_fin(hoy) = saldo_actual

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
            # saldo_inicio(d) = saldo_fin(d) + g + c - a
            saldo_inicio_d = saldo_fin[d] + g + c - a
            # saldo_fin del día anterior es saldo_inicio de hoy
            saldo_fin[dias[i - 1]] = saldo_inicio_d

        # Armar resultado
        resultado = []
        for d in dias:
            g = gastos_map.get(d, 0)
            c = envios_map.get(d, 0) + nomina_map.get(d, 0) + compras_map.get(d, 0)
            a = abonos_map.get(d, 0)
            si = saldo_fin[d] + g + c - a  # saldo_inicio = saldo_fin + salidas - entradas
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


def obtener_cuentas_por_pagar(rol):
    conexion = None
    cursor = None
    try:
        conexion = obtener_conexion(rol)
        cursor = conexion.cursor(dictionary=True)
        consulta = """
            SELECT 
                c.idCompra, 
                c.fechacompra, 
                p.nombre AS proveedor,
                COALESCE(SUM(dc.cantidad * prod.precio_compra), 0) AS total_productos,
                COALESCE(e.valor, 0) AS total_envio,
                (COALESCE(SUM(dc.cantidad * prod.precio_compra), 0) + COALESCE(e.valor, 0)) AS total_compra,
                CASE WHEN e.idEnvio IS NULL THEN 'Pendiente Envío' ELSE 'Envío Registrado' END AS estado_envio
            FROM COMPRA c
            JOIN PROVEEDOR p ON c.idProveedor = p.idProveedor
            LEFT JOIN DETALLE_COMPRA dc ON c.idCompra = dc.idCompra
            LEFT JOIN PRODUCTO prod ON dc.idProducto = prod.idProducto
            LEFT JOIN ENVIO e ON c.idCompra = e.idCompra
            GROUP BY c.idCompra, c.fechacompra, p.nombre, e.valor, e.idEnvio
            ORDER BY c.fechacompra DESC
        """
        cursor.execute(consulta)
        return cursor.fetchall()
    except Error as e:
        raise Exception(f"Error al obtener cuentas por pagar: {e}")
    finally:
        if cursor is not None: cursor.close()
        if conexion is not None and conexion.is_connected(): conexion.close()


# ---------------------------------------------------------------------------
# MÓDULO PROVEEDORES — CRUD Y CONSULTAS
# ---------------------------------------------------------------------------

def obtener_proveedores_completos(rol):
    """
    Obtiene todos los proveedores con todos sus campos (incluyendo contacto)
    para precargar formularios de edición y mostrar la lista de proveedores.

    Retorna:
        list[dict]: idProveedor, nombre, nit, telefono, correo, direccion.
    """
    conexion = None
    cursor = None
    try:
        conexion = obtener_conexion(rol)
        cursor = conexion.cursor(dictionary=True)
        cursor.execute("""
            SELECT idProveedor, nombre, nit, telefono, correo, direccion
            FROM PROVEEDOR
            ORDER BY nombre
        """)
        return cursor.fetchall()
    except Error as e:
        raise Exception(f"Error al obtener proveedores: {e}")
    finally:
        if cursor is not None: cursor.close()
        if conexion is not None and conexion.is_connected(): conexion.close()


def insertar_proveedor(nombre, nit, telefono, correo, direccion, rol):
    """
    Inserta un nuevo proveedor en la base de datos.
    Solo accesible por el rol Gerente (rol = 1).

    Retorna:
        int: El idProveedor autogenerado.
    """
    nombre    = nombre.strip()
    nit       = nit.strip()       if nit       and nit.strip()       else None
    telefono  = telefono.strip()  if telefono  and telefono.strip()  else None
    correo    = correo.strip()    if correo    and correo.strip()    else None
    direccion = direccion.strip() if direccion and direccion.strip() else None

    conexion = None
    cursor = None
    try:
        conexion = obtener_conexion(rol)
        cursor = conexion.cursor()
        cursor.execute(
            "INSERT INTO PROVEEDOR (nombre, nit, telefono, correo, direccion) VALUES (%s, %s, %s, %s, %s)",
            (nombre, nit, telefono, correo, direccion)
        )
        conexion.commit()
        return cursor.lastrowid
    except Error as e:
        if e.errno == 1062:
            raise Exception("El nombre o teléfono ya está registrado para otro proveedor.")
        raise Exception(f"Error al registrar proveedor: {e}")
    finally:
        if cursor is not None: cursor.close()
        if conexion is not None and conexion.is_connected(): conexion.close()


def actualizar_proveedor(id_proveedor, nombre, nit, telefono, correo, direccion, rol):
    """
    Actualiza los datos de un proveedor existente.
    Solo accesible por el rol Gerente (rol = 1).
    """
    nombre    = nombre.strip()
    nit       = nit.strip()       if nit       and nit.strip()       else None
    telefono  = telefono.strip()  if telefono  and telefono.strip()  else None
    correo    = correo.strip()    if correo    and correo.strip()    else None
    direccion = direccion.strip() if direccion and direccion.strip() else None

    conexion = None
    cursor = None
    try:
        conexion = obtener_conexion(rol)
        cursor = conexion.cursor()
        cursor.execute(
            """UPDATE PROVEEDOR
               SET nombre = %s, nit = %s, telefono = %s, correo = %s, direccion = %s
               WHERE idProveedor = %s""",
            (nombre, nit, telefono, correo, direccion, id_proveedor)
        )
        conexion.commit()
    except Error as e:
        if e.errno == 1062:
            raise Exception("El nombre o teléfono ya está registrado para otro proveedor.")
        raise Exception(f"Error al actualizar proveedor: {e}")
    finally:
        if cursor is not None: cursor.close()
        if conexion is not None and conexion.is_connected(): conexion.close()


def obtener_compras_sin_envio_por_proveedor(id_proveedor, rol):
    """
    Obtiene las compras de un proveedor que aún NO tienen un envío asignado.
    Estas son las compras pendientes de despacho/pago.

    Retorna:
        list[dict]: idCompra, fechacompra, total_productos, total_unidades,
                    y 'detalle' (lista de productos: nombre, referencia, cantidad, precio_compra).
    """
    conexion = None
    cursor = None
    try:
        conexion = obtener_conexion(rol)
        cursor = conexion.cursor(dictionary=True)

        # Compras sin envío asociado
        cursor.execute("""
            SELECT
                c.idCompra,
                c.fechacompra,
                COALESCE(SUM(dc.cantidad * p.precio_compra), 0) AS total_productos,
                COALESCE(SUM(dc.cantidad), 0)                   AS total_unidades
            FROM COMPRA c
            LEFT JOIN DETALLE_COMPRA dc ON c.idCompra  = dc.idCompra
            LEFT JOIN PRODUCTO p        ON dc.idProducto = p.idProducto
            LEFT JOIN ENVIO e           ON c.idCompra  = e.idCompra
            WHERE c.idProveedor = %s
              AND e.idEnvio IS NULL
            GROUP BY c.idCompra, c.fechacompra
            ORDER BY c.fechacompra DESC
        """, (id_proveedor,))
        compras = cursor.fetchall()

        # Detalle de productos por cada compra
        for compra in compras:
            cursor.execute("""
                SELECT p.nombre, p.referencia, dc.cantidad,
                       p.precio_compra,
                       (dc.cantidad * p.precio_compra) AS subtotal
                FROM DETALLE_COMPRA dc
                JOIN PRODUCTO p ON dc.idProducto = p.idProducto
                WHERE dc.idCompra = %s
            """, (compra['idCompra'],))
            compra['detalle'] = cursor.fetchall()

        return compras
    except Exception as e:
        raise Exception(f"Error al obtener compras pendientes del proveedor: {e}")
    finally:
        if cursor is not None: cursor.close()
        if conexion is not None and conexion.is_connected(): conexion.close()


def obtener_productos_para_compra(rol):
    """
    Obtiene productos con precio de compra para el formulario de nueva compra.
    Solo accesible por el rol Gerente.

    Retorna:
        list[dict]: idProducto, nombre, referencia, precio_compra.
    """
    conexion = None
    cursor = None
    try:
        conexion = obtener_conexion(rol)
        cursor = conexion.cursor(dictionary=True)
        cursor.execute("""
            SELECT idProducto, nombre, referencia, precio_compra
            FROM PRODUCTO
            ORDER BY nombre
        """)
        return cursor.fetchall()
    except Error as e:
        raise Exception(f"Error al obtener productos para compra: {e}")
    finally:
        if cursor is not None: cursor.close()
        if conexion is not None and conexion.is_connected(): conexion.close()


def insertar_compra(id_proveedor, id_empleado, productos, rol):
    """
    Registra una nueva compra y su detalle en una transacción atómica.

    IMPORTANTE: Esta función NO actualiza el inventario (PRODUCTO.bodega).
    El inventario se actualiza al confirmar el envío (insertar_envio),
    distribuyendo el costo del envío entre el total de unidades compradas
    para ajustar el precio_compra de cada producto.

    Parámetros:
        id_proveedor (int): Proveedor al que se le compra.
        id_empleado  (int): Gerente que registra la compra.
        productos (list[dict]): Lista de {'idProducto': int, 'cantidad': int}.
        rol (int): Debe ser 1 (Gerente).

    Retorna:
        int: El idCompra autogenerado.
    """
    conexion = None
    cursor = None
    try:
        conexion = obtener_conexion(rol)
        cursor = conexion.cursor()

        # 1. Cabecera de la compra
        cursor.execute(
            "INSERT INTO COMPRA (idEmpleado, idProveedor) VALUES (%s, %s)",
            (id_empleado, id_proveedor)
        )
        id_compra = cursor.lastrowid

        # 2. Detalle por cada producto
        for prod in productos:
            cursor.execute(
                "INSERT INTO DETALLE_COMPRA (idProducto, idCompra, cantidad) VALUES (%s, %s, %s)",
                (prod['idProducto'], id_compra, prod['cantidad'])
            )

        conexion.commit()
        return id_compra
    except Error as e:
        if conexion:
            conexion.rollback()
        raise Exception(f"Error al registrar la compra: {e}")
    except Exception as e:
        if conexion:
            conexion.rollback()
        raise e
    finally:
        if cursor is not None: cursor.close()
        if conexion is not None and conexion.is_connected(): conexion.close()

def registrar_venta(id_empleado, id_cliente, productos, id_metodo_pago, monto_pagado, estado_pago, valor_total, rol):
    """
    Registra una nueva venta y sus detalles en una transacción.
    Si se recibe un pago total o parcial, registra el abono y actualiza
    el saldo del método de pago.
    Actualiza el inventario restando las cantidades vendidas.
    
    productos: list[dict] con llaves 'idProducto', 'cantidad'.
    """
    conexion = None
    cursor = None
    try:
        from database.connection import obtener_conexion
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

