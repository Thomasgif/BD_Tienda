import psycopg2
from psycopg2.extras import execute_values
from database.base import db_cursor, _convertir_filas, SmartDict


def obtener_proveedores(rol=None):
    """Obtiene la lista simple de proveedores."""
    try:
        with db_cursor(commit=False, dictionary=True) as (cursor, _):
            cursor.execute("SELECT idProveedor, nombre, nit FROM PROVEEDOR WHERE estado = TRUE ORDER BY nombre")
            proveedores = cursor.fetchall()
            return _convertir_filas(proveedores) or []
    except Exception as e:
        raise Exception(f"Error al obtener proveedores: {e}")


def obtener_compras(rol=None):
    """Obtiene la lista general de compras."""
    try:
        with db_cursor(commit=False, dictionary=True) as (cursor, _):
            cursor.execute("SELECT idCompra, fechacompra, idProveedor FROM COMPRA ORDER BY fechacompra DESC")
            compras = cursor.fetchall()
            return _convertir_filas(compras) or []
    except Exception as e:
        raise Exception(f"Error al obtener compras: {e}")


def obtener_pedidos_proveedor(id_proveedor, rol=None):
    """Obtiene el histórico de compras y estado de flete para un proveedor específico."""
    try:
        with db_cursor(commit=False, dictionary=True) as (cursor, _):
            consulta = """
                SELECT c.idCompra, c.fechacompra, e.idEnvio, e.fecha AS fecha_envio, COALESCE(e.valor, 0) as valor
                FROM COMPRA c
                LEFT JOIN ENVIO e ON c.idCompra = e.idCompra
                WHERE c.idProveedor = %s
                ORDER BY c.fechacompra DESC
            """
            cursor.execute(consulta, (id_proveedor,))
            pedidos = cursor.fetchall()
            return _convertir_filas(pedidos) or []
    except Exception as e:
        raise Exception(f"Error al obtener pedidos del proveedor: {e}")


def obtener_proveedores_completos(rol=None):
    """Obtiene el listado detallado de proveedores con datos de contacto."""
    try:
        with db_cursor(commit=False, dictionary=True) as (cursor, _):
            cursor.execute("""
                SELECT idProveedor, nombre, nit, telefono, correo, direccion, estado
                FROM PROVEEDOR
                ORDER BY nombre
            """)
            proveedores = cursor.fetchall()
            return _convertir_filas(proveedores) or []
    except Exception as e:
        raise Exception(f"Error al obtener proveedores: {e}")


def insertar_proveedor(nombre, nit, telefono, correo, direccion, rol=None):
    """Registra un nuevo proveedor en la base de datos."""
    nombre    = nombre.strip()
    nit       = nit.strip()       if nit       and nit.strip()       else None
    telefono  = telefono.strip()  if telefono  and telefono.strip()  else None
    correo    = correo.strip()    if correo    and correo.strip()    else None
    direccion = direccion.strip() if direccion and direccion.strip() else None

    try:
        with db_cursor(commit=True, dictionary=True) as (cursor, _):
            cursor.execute(
                """INSERT INTO PROVEEDOR (nombre, nit, telefono, correo, direccion, estado) 
                   VALUES (%s, %s, %s, %s, %s, TRUE)
                   RETURNING idProveedor""",
                (nombre, nit, telefono, correo, direccion)
            )
            nuevo = cursor.fetchone()
            return nuevo['idproveedor'] if nuevo and 'idproveedor' in nuevo else (nuevo['idProveedor'] if nuevo else None)
    except psycopg2.IntegrityError as e:
        if "unique" in str(e).lower():
            raise Exception("El nombre o teléfono ya está registrado para otro proveedor.")
        raise Exception(f"Error al registrar proveedor: {e}")
    except Exception as e:
        if "unique" in str(e).lower():
            raise Exception("El nombre o teléfono ya está registrado para otro proveedor.")
        raise Exception(f"Error al registrar proveedor: {e}")


def actualizar_proveedor(id_proveedor, nombre, nit, telefono, correo, direccion, rol=None):
    """Actualiza la información de un proveedor existente."""
    nombre    = nombre.strip()
    nit       = nit.strip()       if nit       and nit.strip()       else None
    telefono  = telefono.strip()  if telefono  and telefono.strip()  else None
    correo    = correo.strip()    if correo    and correo.strip()    else None
    direccion = direccion.strip() if direccion and direccion.strip() else None

    try:
        with db_cursor(commit=True, dictionary=True) as (cursor, _):
            cursor.execute(
                """UPDATE PROVEEDOR
                   SET nombre = %s, nit = %s, telefono = %s, correo = %s, direccion = %s
                   WHERE idProveedor = %s""",
                (nombre, nit, telefono, correo, direccion, id_proveedor)
            )
    except psycopg2.IntegrityError as e:
        if "unique" in str(e).lower():
            raise Exception("El nombre o teléfono ya está registrado para otro proveedor.")
        raise Exception(f"Error al actualizar proveedor: {e}")
    except Exception as e:
        if "unique" in str(e).lower():
            raise Exception("El nombre o teléfono ya está registrado para otro proveedor.")
        raise Exception(f"Error al actualizar proveedor: {e}")


def obtener_compras_sin_envio_por_proveedor(id_proveedor, rol=None):
    """
    Obtiene las compras pendientes de flete/envío de un proveedor junto con todos sus
    detalles en UNA SOLA consulta optimizada utilizando agregación JSON nativa de PostgreSQL.
    """
    try:
        with db_cursor(commit=False, dictionary=True) as (cursor, _):
            consulta = """
                SELECT
                    c.idCompra,
                    c.fechacompra,
                    COALESCE(SUM(dc.cantidad * dc.precio_unit), 0) AS total_productos,
                    COALESCE(SUM(dc.cantidad), 0)                   AS total_unidades,
                    COALESCE(
                        json_agg(
                            json_build_object(
                                'nombre', p.nombre,
                                'referencia', p.referencia,
                                'cantidad', dc.cantidad,
                                'precio_compra', dc.precio_unit,
                                'subtotal', (dc.cantidad * dc.precio_unit)
                            )
                        ) FILTER (WHERE dc.idDetalle_compra IS NOT NULL),
                        '[]'::json
                    ) AS detalle
                FROM COMPRA c
                LEFT JOIN DETALLE_COMPRA dc ON c.idCompra  = dc.idCompra
                LEFT JOIN PRODUCTO p        ON dc.idProducto = p.idProducto
                LEFT JOIN ENVIO e           ON c.idCompra  = e.idCompra
                WHERE c.idProveedor = %s
                  AND e.idEnvio IS NULL
                GROUP BY c.idCompra, c.fechacompra
                ORDER BY c.fechacompra DESC
            """
            cursor.execute(consulta, (id_proveedor,))
            compras = cursor.fetchall()
            return _convertir_filas(compras) or []
    except Exception as e:
        raise Exception(f"Error al obtener compras pendientes del proveedor: {e}")


def insertar_compra(id_proveedor, id_empleado, productos, id_metodo_pago, total, rol=None):
    """
    Registra una orden de compra a proveedor en Supabase, descontando el saldo de la empresa
    e insertando los detalles en bloque.
    """
    total = float(total)
    try:
        with db_cursor(commit=True, dictionary=True) as (cursor, _):
            # 1. Descontar del saldo de la cuenta
            cursor.execute(
                "UPDATE METODO_DE_PAGO SET saldo = saldo - %s WHERE idMetodo_de_pago = %s",
                (total, id_metodo_pago)
            )

            # 2. Insertar cabecera de la compra
            cursor.execute(
                "INSERT INTO COMPRA (idEmpleado, idProveedor, idMetodo_de_pago, total) VALUES (%s, %s, %s, %s) RETURNING idCompra",
                (id_empleado, id_proveedor, id_metodo_pago, total)
            )
            res_compra = cursor.fetchone()
            id_compra = res_compra['idcompra'] if res_compra and 'idcompra' in res_compra else res_compra['idCompra']

            # 3. Inserción en lote de detalles
            detalles_tuples = [(p['idProducto'], id_compra, p['cantidad'], p['precio_compra']) for p in productos]
            execute_values(
                cursor,
                "INSERT INTO DETALLE_COMPRA (idProducto, idCompra, cantidad, precio_unit) VALUES %s",
                detalles_tuples
            )

            return id_compra
    except Exception as e:
        err_msg = str(e).lower()
        if "check" in err_msg or "violates" in err_msg or "saldo" in err_msg:
            raise Exception("Saldo insuficiente en la cuenta para realizar la compra.")
        raise Exception(f"Error al registrar la compra: {e}")


def obtener_detalle_compra(idCompra, rol=None):
    """Obtiene los detalles de artículos adquiridos en una compra."""
    try:
        with db_cursor(commit=False, dictionary=True) as (cursor, _):
            consulta = """
                SELECT p.nombre, p.referencia, d.cantidad, d.precio_unit as precio_compra, (d.cantidad * d.precio_unit) as subtotal
                FROM DETALLE_COMPRA d
                JOIN PRODUCTO p ON d.idProducto = p.idProducto
                WHERE d.idCompra = %s
            """
            cursor.execute(consulta, (idCompra,))
            detalles = cursor.fetchall()
            return _convertir_filas(detalles) or []
    except Exception as e:
        raise Exception(f"Error al obtener detalle de compra: {e}")
