import psycopg2
from database.base import db_cursor, _convertir_filas, SmartDict


def obtener_clientes(rol=None):
    """Obtiene la lista completa de clientes registrados."""
    try:
        with db_cursor(commit=False, dictionary=True) as (cursor, _):
            cursor.execute("""
                SELECT idCliente, nombre, apellidos, documento, telefono, correo, direccion 
                FROM CLIENTE 
                ORDER BY nombre, apellidos
            """)
            clientes = cursor.fetchall()
            return _convertir_filas(clientes) or []
    except Exception as e:
        raise Exception(f"Error al obtener clientes: {e}")


def insertar_cliente(nombre, apellidos, documento, rol=None, telefono=None, correo=None, direccion=None):
    """Inserta un nuevo cliente y retorna su ID asignado en Supabase."""
    telefono = telefono.strip() if telefono and telefono.strip() else None
    correo = correo.strip() if correo and correo.strip() else None
    direccion = direccion.strip() if direccion and direccion.strip() else None
    nombre = nombre.strip()
    apellidos = apellidos.strip()
    documento = documento.strip()

    try:
        with db_cursor(commit=True, dictionary=True) as (cursor, _):
            consulta = """
                INSERT INTO CLIENTE (nombre, apellidos, documento, telefono, correo, direccion)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING idCliente
            """
            cursor.execute(consulta, (nombre, apellidos, documento, telefono, correo, direccion))
            nuevo = cursor.fetchone()
            return nuevo['idcliente'] if nuevo and 'idcliente' in nuevo else (nuevo['idCliente'] if nuevo else None)
    except psycopg2.IntegrityError as e:
        if "unique" in str(e).lower() or "documento" in str(e).lower():
            raise Exception("El documento ingresado ya está registrado para otro cliente.")
        raise Exception(f"Error al registrar cliente: {e}")
    except Exception as e:
        if "unique" in str(e).lower() or "documento" in str(e).lower():
            raise Exception("El documento ingresado ya está registrado para otro cliente.")
        raise Exception(f"Error al registrar cliente en la base de datos: {e}")


def actualizar_cliente(id_cliente, nombre, apellidos, documento, rol=None, telefono=None, correo=None, direccion=None):
    """Actualiza la información de un cliente existente."""
    telefono = telefono.strip() if telefono and telefono.strip() else None
    correo = correo.strip() if correo and correo.strip() else None
    direccion = direccion.strip() if direccion and direccion.strip() else None
    nombre = nombre.strip()
    apellidos = apellidos.strip()
    documento = documento.strip()

    try:
        with db_cursor(commit=True, dictionary=True) as (cursor, _):
            consulta = """
                UPDATE CLIENTE 
                SET nombre = %s, apellidos = %s, documento = %s, telefono = %s, correo = %s, direccion = %s
                WHERE idCliente = %s
            """
            cursor.execute(consulta, (nombre, apellidos, documento, telefono, correo, direccion, id_cliente))
    except psycopg2.IntegrityError as e:
        if "unique" in str(e).lower() or "documento" in str(e).lower():
            raise Exception("El documento ingresado ya está registrado para otro cliente.")
        raise Exception(f"Error al actualizar cliente: {e}")
    except Exception as e:
        if "unique" in str(e).lower() or "documento" in str(e).lower():
            raise Exception("El documento ingresado ya está registrado para otro cliente.")
        raise Exception(f"Error al actualizar cliente en la base de datos: {e}")


def obtener_deudas_cliente(idcli, rol=None):
    """
    Obtiene las deudas pendientes de un cliente en una sola consulta optimizada,
    calculando monto total, monto abonado y saldo pendiente.
    """
    try:
        with db_cursor(commit=False, dictionary=True) as (cursor, _):
            cursor.execute("""
                SELECT 
                    v.idVenta, 
                    v.fecha_venta, 
                    v.valor_total,
                    COALESCE(SUM(p.monto), 0) AS total_pagado,
                    (v.valor_total - COALESCE(SUM(p.monto), 0)) AS saldo_pendiente
                FROM VENTA v
                LEFT JOIN PAGO p ON v.idVenta = p.idVenta
                WHERE v.idCliente = %s AND v.estado_pago = 'PENDIENTE'
                GROUP BY v.idVenta, v.fecha_venta, v.valor_total
                ORDER BY v.fecha_venta DESC
            """, (idcli,))
            deudas = cursor.fetchall()
            return _convertir_filas(deudas) or []
    except Exception as e:
        raise Exception(f"Error al obtener deudas del cliente: {e}")
