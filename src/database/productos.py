from mysql.connector import Error
from math import isfinite
from database.base import obtener_conexion


def obtener_productos(rol):
    conexion = None
    cursor = None
    try:
        conexion = obtener_conexion(rol)
        cursor = conexion.cursor(dictionary=True)
        cursor.execute("SELECT idProducto, nombre, referencia, precio_compra, precio_venta, bodega, descripcion FROM PRODUCTO")
        productos = cursor.fetchall()
        return productos
    except Error as e:
        raise Exception(f"Error al obtener productos: {e}")
    finally:
        if cursor is not None:
            cursor.close()
        if conexion is not None and conexion.is_connected():
            conexion.close()


def obtener_productos_para_compra(rol):
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


def insertar_producto(nombre, referencia, precio_compra, precio_venta, descripcion, rol):
    nombre = nombre.strip()
    referencia = referencia.strip()
    descripcion = descripcion.strip()
    
    conexion = None
    cursor = None
    try:
        conexion = obtener_conexion(rol)
        cursor = conexion.cursor()
        
        consulta = """
            INSERT INTO PRODUCTO (nombre, referencia, precio_compra, precio_venta, bodega, descripcion)
            VALUES (%s, %s, %s, %s, 0, %s)
        """
        valores = (nombre, referencia, precio_compra, precio_venta, descripcion)
        cursor.execute(consulta, valores)
        conexion.commit()
        return cursor.lastrowid
    except Error as e:
        if e.errno == 1062:
            raise Exception("El nombre o referencia del producto ya está registrado.")
        raise Exception(f"Error al registrar producto: {e}")
    finally:
        if cursor is not None: cursor.close()
        if conexion is not None and conexion.is_connected(): conexion.close()


def actualizar_precio_producto(id_producto, precio_venta, rol):
    if rol != 1:
        raise Exception("Permiso denegado. Solo el gerente puede actualizar precios de venta.")
    
    try:
        precio_venta = float(precio_venta)
        if precio_venta <= 0 or not isfinite(precio_venta):
            raise ValueError()
    except ValueError:
        raise Exception("El precio de venta debe ser un número positivo válido.")

    conexion = None
    cursor = None
    try:
        conexion = obtener_conexion(rol)
        cursor = conexion.cursor()
        
        consulta = """
            UPDATE PRODUCTO 
            SET precio_venta = %s
            WHERE idProducto = %s
        """
        cursor.execute(consulta, (precio_venta, id_producto))
        conexion.commit()
    except Error as e:
        raise Exception(f"Error al actualizar precio del producto: {e}")
    finally:
        if cursor is not None:
            cursor.close()
        if conexion is not None and conexion.is_connected():
            conexion.close()
