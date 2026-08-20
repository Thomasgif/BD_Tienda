from math import isfinite
import psycopg2
from database.base import db_cursor, _convertir_filas


def obtener_productos(rol=None):
    """Obtiene el catálogo completo de productos con stock y precios."""
    try:
        with db_cursor(commit=False, dictionary=True) as (cursor, _):
            cursor.execute("""
                SELECT idProducto, nombre, referencia, precio_compra, precio_venta, bodega, descripcion 
                FROM PRODUCTO
                ORDER BY nombre
            """)
            productos = cursor.fetchall()
            return _convertir_filas(productos) or []
    except Exception as e:
        raise Exception(f"Error al obtener productos: {e}")


def obtener_productos_para_compra(rol=None):
    """Obtiene productos disponibles para abastecimiento ordenados alfabéticamente."""
    try:
        with db_cursor(commit=False, dictionary=True) as (cursor, _):
            cursor.execute("""
                SELECT idProducto, nombre, referencia, precio_compra
                FROM PRODUCTO
                ORDER BY nombre
            """)
            productos = cursor.fetchall()
            return _convertir_filas(productos) or []
    except Exception as e:
        raise Exception(f"Error al obtener productos para compra: {e}")


def insertar_producto(nombre, referencia, precio_compra, precio_venta, descripcion, rol=None):
    """Inserta un nuevo producto en el catálogo y devuelve su ID generado."""
    nombre = nombre.strip()
    referencia = referencia.strip()
    descripcion = descripcion.strip()
    
    try:
        with db_cursor(commit=True, dictionary=True) as (cursor, _):
            consulta = """
                INSERT INTO PRODUCTO (nombre, referencia, precio_compra, precio_venta, bodega, descripcion)
                VALUES (%s, %s, %s, %s, 0, %s)
                RETURNING idProducto
            """
            cursor.execute(consulta, (nombre, referencia, precio_compra, precio_venta, descripcion))
            nuevo = cursor.fetchone()
            return nuevo['idproducto'] if nuevo and 'idproducto' in nuevo else (nuevo['idProducto'] if nuevo else None)
    except psycopg2.IntegrityError as e:
        if "unique" in str(e).lower():
            raise Exception("El nombre o referencia del producto ya está registrado.")
        raise Exception(f"Error al registrar producto: {e}")
    except Exception as e:
        if "unique" in str(e).lower():
            raise Exception("El nombre o referencia del producto ya está registrado.")
        raise Exception(f"Error al registrar producto: {e}")


def actualizar_precio_producto(id_producto, precio_venta, rol=None):
    """Actualiza el precio de venta de un producto (solo permitido a gerente)."""
    if rol is not None and rol != 1:
        raise Exception("Permiso denegado. Solo el gerente puede actualizar precios de venta.")
    
    try:
        precio_venta = float(precio_venta)
        if precio_venta <= 0 or not isfinite(precio_venta):
            raise ValueError()
    except ValueError:
        raise Exception("El precio de venta debe ser un número positivo válido.")

    try:
        with db_cursor(commit=True, dictionary=True) as (cursor, _):
            consulta = """
                UPDATE PRODUCTO 
                SET precio_venta = %s
                WHERE idProducto = %s
            """
            cursor.execute(consulta, (precio_venta, id_producto))
    except Exception as e:
        raise Exception(f"Error al actualizar precio del producto: {e}")
