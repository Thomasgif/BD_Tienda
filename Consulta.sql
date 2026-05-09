CREATE DATABASE IF NOT EXISTS BD_Tienda;

USE BD_Tienda;

create table BD_Tienda.PROVEEDOR (
    idProveedor INT auto_increment not null,
    nombre varchar(20) not null unique,
    telefono varchar(15) null unique,
    correo varchar(30) null,
    estado bit,
    nit varchar(10) null,
    direccion varchar(50) null,
    constraint proveedor_pk primary key (idProveedor)
)

go

create table BD_Tienda.PRODUCTO (
    idProducto INT auto_increment not null,
    nombre varchar(20) not null,
    referencia varchar(20) not null,
    precio_compra NUMERIC not null,
    precio_venta NUMERIC not null,
    bodega INT null,
    descripcion varchar(128) not null,
    constraint PRODUCTO_pk primary key (idProducto)
)

go

create table BD_Tienda.CUENTA_EMPRESA (
    idCuenta_empresa INT auto_increment not null,
    idProveedor INT references PROVEEDOR (idProveedor),
    referencia varchar(20) not null,
    precio_compra NUMERIC not null,
    precio_venta NUMERIC not null,
    bodega INT null,
    descripcion varchar(128) not null,
    constraint PRODUCTO_pk primary key (idCuenta_empresa)
)

go

create table BD_Tienda.EMPLEADO (
    idEmpleado INT auto_increment not null,
    nombre varchar(20) not null,
    documento varchar(20) null,
    treabajo_hora NUMERIC not null,
    pago_hora NUMERIC not null,
    telefono varchar(15) null,
    correo varchar(30) null,
    constraint PRODUCTO_pk primary key (idEmpleado)
)

go

create table BD_Tienda.COMPRA (
    idCompra INT auto_increment not null,
    idEmpleado references EMPLEADO (idEmpleado),
    idProveedor references PROVEEDOR (idProveedor),
    fechacompra TIMESTAMP not null
)

go

create table BD_Tienda.DETALLE_COMPRA (
    idDetalle_compra INT auto_increment not null,
    idProducto references PRODUCTO (idProducto),
    idCompra references COMPRA (idCompra),
    cantidad INT null,
    constraint PRODUCTO_pk primary key (idDetalle_compra)
)

go

create table BD_Tienda.CLIENTE (
    idCliente INT auto_increment not null,
    nombre varchar(20) not null,
    apellidos varchar(50) not null,
    documento varchar(11) not null unique,
    telefono varchar(15) null,
    correo varchar(30) null,
    direccion varchar(50) null,
    constraint PRODUCTO_pk primary key (idCliente)
)

go

create table BD_Tienda.METODO_DE_PAGO (
    idMetodo_de_pago INT auto_increment not null,
    nombre varchar(20) not null,
    num_cuenta varchar(16) not null unique,
    constraint PRODUCTO_pk primary key (idMetodo_de_pago)
)

go

create table BD_Tienda.VENTA (
    idVenta INT auto_increment not null,
    idEmpleado references EMPLEADO (idEmpleado),
    fecha_venta TIMESTAMP not null,
    estado_pago varchar(10) not null,
    valor_total numeric not null,
    constraint PRODUCTO_pk primary key (idVenta)
)

go

create table BD_Tienda.PAGO (
    idPago INT auto_increment not null,
    idCliente references CLIENTE (idCliente),
    idVenta references VENTA (idVenta),
    idMetodo_de_pago references METODO_DE_PAGO (idMetodo_de_pago),
    monto numeric not null,
    fecha_pago TIMESTAMP,
    constraint PRODUCTO_pk primary key (idPago)
)

go

create table BD_Tienda.DETALLE_VENTA (
    idDetalle_venta INT auto_increment not null,
    idProducto references PRODUCTO (idproducto),
    idVenta references VENTA (idVenta),
    cantidad INT not null,
    constraint PRODUCTO_pk primary key (idPago)
)