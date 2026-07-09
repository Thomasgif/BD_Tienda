from database.base import (
    obtener_conexion,
    validar_credenciales
)
from database.clientes import (
    obtener_clientes,
    insertar_cliente,
    actualizar_cliente,
    obtener_deudas_cliente
)
from database.productos import (
    obtener_productos,
    obtener_productos_para_compra,
    insertar_producto,
    actualizar_precio_producto
)
from database.ventas import (
    pago_total_venta,
    pagar_venta_pendiente,
    cancelar_venta,
    registrar_venta,
    obtener_ventas_cliente,
    obtener_detalle_venta,
    registrar_devolucion_cambio
)
from database.cuentas import (
    obtener_saldos_cuentas,
    obtener_gastos,
    insertar_gasto,
    obtener_resumen_financiero_7dias,
    obtener_cuentas_por_cobrar
)
from database.proveedores import (
    obtener_proveedores,
    obtener_compras,
    obtener_pedidos_proveedor,
    obtener_proveedores_completos,
    insertar_proveedor,
    actualizar_proveedor,
    obtener_compras_sin_envio_por_proveedor,
    insertar_compra,
    obtener_detalle_compra
)
from database.envios import (
    obtener_envios_list,
    insertar_envio
)
from database.empleados import (
    obtener_empleados,
    obtener_ventas_mes_empleado,
    pagar_empleado,
    insertar_empleado,
    actualizar_empleado,
    eliminar_empleado
)
