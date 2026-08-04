from mysql.connector import Error
from database.base import obtener_conexion


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


def obtener_proveedores_completos(rol):
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
    conexion = None
    cursor = None
    try:
        conexion = obtener_conexion(rol)
        cursor = conexion.cursor(dictionary=True)

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


def insertar_compra(id_proveedor, id_empleado, productos, id_metodo_pago, total, rol):
    conexion = None
    cursor = None
    try:
        conexion = obtener_conexion(rol)
        cursor = conexion.cursor()

        # 1. Restar del saldo de la cuenta de la empresa
        cursor.execute(
            "UPDATE METODO_DE_PAGO SET saldo = saldo - %s WHERE idMetodo_de_pago = %s",
            (total, id_metodo_pago)
        )

        # 2. Cabecera de la compra
        cursor.execute(
            "INSERT INTO COMPRA (idEmpleado, idProveedor, idMetodo_de_pago, total) VALUES (%s, %s, %s, %s)",
            (id_empleado, id_proveedor, id_metodo_pago, total)
        )
        id_compra = cursor.lastrowid

        # 3. Detalle por cada producto
        for prod in productos:
            cursor.execute(
                "INSERT INTO DETALLE_COMPRA (idProducto, idCompra, cantidad, precio_unit) VALUES (%s, %s, %s, %s)",
                (prod['idProducto'], id_compra, prod['cantidad'], prod['precio_compra'])
            )

        conexion.commit()
        return id_compra
    except Error as e:
        if conexion:
            conexion.rollback()
        if e.errno == 3819 or "CONSTRAINT" in str(e).upper() or "check constraint" in str(e).lower():
            raise Exception("Saldo insuficiente en la cuenta para realizar la compra.")
        raise Exception(f"Error al registrar la compra: {e}")
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
