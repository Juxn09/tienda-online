/* =========================================================
   Tienda en línea - Script 01: creación de la base y tablas
   Ejecutar en SSMS completo (F5). Se puede re-ejecutar.
   ========================================================= */

-- 1. Crear la base de datos solo si no existe
IF DB_ID('TiendaOnline') IS NULL
    CREATE DATABASE TiendaOnline;
GO

USE TiendaOnline;
GO

-- 2. Borrar tablas si ya existen (hijas primero, padres al final)
DROP TABLE IF EXISTS Resena;
DROP TABLE IF EXISTS Envio;
DROP TABLE IF EXISTS Pago;
DROP TABLE IF EXISTS DetallePedido;
DROP TABLE IF EXISTS Pedido;
DROP TABLE IF EXISTS Direccion;
DROP TABLE IF EXISTS Cliente;
DROP TABLE IF EXISTS Producto;
DROP TABLE IF EXISTS Proveedor;
DROP TABLE IF EXISTS Categoria;
GO

-- 3. Catálogos ------------------------------------------------
CREATE TABLE Categoria (
    id_categoria  INT IDENTITY(1,1) NOT NULL,
    nombre        NVARCHAR(60)  NOT NULL,
    descripcion   NVARCHAR(200) NULL,
    CONSTRAINT PK_Categoria PRIMARY KEY (id_categoria),
    CONSTRAINT UQ_Categoria_nombre UNIQUE (nombre)
);

CREATE TABLE Proveedor (
    id_proveedor  INT IDENTITY(1,1) NOT NULL,
    nit           VARCHAR(15)   NOT NULL,
    razon_social  NVARCHAR(100) NOT NULL,
    ciudad        NVARCHAR(60)  NOT NULL,
    telefono      VARCHAR(20)   NULL,
    email         VARCHAR(100)  NULL,
    CONSTRAINT PK_Proveedor PRIMARY KEY (id_proveedor),
    CONSTRAINT UQ_Proveedor_nit UNIQUE (nit)
);

-- 4. Maestros -------------------------------------------------
CREATE TABLE Producto (
    id_producto   INT IDENTITY(1,1) NOT NULL,
    sku           VARCHAR(20)    NOT NULL,
    nombre        NVARCHAR(120)  NOT NULL,
    descripcion   NVARCHAR(300)  NULL,
    precio        DECIMAL(12,2)  NOT NULL,
    stock         INT            NOT NULL CONSTRAINT DF_Producto_stock DEFAULT 0,
    activo        BIT            NOT NULL CONSTRAINT DF_Producto_activo DEFAULT 1,
    id_categoria  INT            NOT NULL,
    id_proveedor  INT            NOT NULL,
    CONSTRAINT PK_Producto PRIMARY KEY (id_producto),
    CONSTRAINT UQ_Producto_sku UNIQUE (sku),
    CONSTRAINT CK_Producto_precio CHECK (precio > 0),
    CONSTRAINT CK_Producto_stock  CHECK (stock >= 0),
    CONSTRAINT FK_Producto_Categoria FOREIGN KEY (id_categoria) REFERENCES Categoria (id_categoria),
    CONSTRAINT FK_Producto_Proveedor FOREIGN KEY (id_proveedor) REFERENCES Proveedor (id_proveedor)
);

CREATE TABLE Cliente (
    id_cliente     INT IDENTITY(1,1) NOT NULL,
    documento      VARCHAR(15)  NOT NULL,
    nombres        NVARCHAR(60) NOT NULL,
    apellidos      NVARCHAR(60) NOT NULL,
    email          VARCHAR(100) NOT NULL,
    telefono       VARCHAR(20)  NULL,
    fecha_registro DATE         NOT NULL,
    CONSTRAINT PK_Cliente PRIMARY KEY (id_cliente),
    CONSTRAINT UQ_Cliente_documento UNIQUE (documento),
    CONSTRAINT UQ_Cliente_email UNIQUE (email)
);

CREATE TABLE Direccion (
    id_direccion  INT IDENTITY(1,1) NOT NULL,
    id_cliente    INT           NOT NULL,
    alias         NVARCHAR(30)  NOT NULL,
    direccion     NVARCHAR(150) NOT NULL,
    ciudad        NVARCHAR(60)  NOT NULL,
    departamento  NVARCHAR(60)  NOT NULL,
    es_principal  BIT           NOT NULL CONSTRAINT DF_Direccion_principal DEFAULT 0,
    CONSTRAINT PK_Direccion PRIMARY KEY (id_direccion),
    CONSTRAINT UQ_Direccion_Cliente UNIQUE (id_direccion, id_cliente),  -- requisito de la FK compuesta
    CONSTRAINT FK_Direccion_Cliente FOREIGN KEY (id_cliente) REFERENCES Cliente (id_cliente)
);

-- 5. Transacciones --------------------------------------------
CREATE TABLE Pedido (
    id_pedido     INT IDENTITY(1,1) NOT NULL,
    id_cliente    INT           NOT NULL,
    id_direccion  INT           NOT NULL,
    fecha_pedido  DATETIME2(0)  NOT NULL,
    estado        VARCHAR(15)   NOT NULL,
    total         DECIMAL(14,2) NOT NULL CONSTRAINT DF_Pedido_total DEFAULT 0,
    CONSTRAINT PK_Pedido PRIMARY KEY (id_pedido),
    CONSTRAINT CK_Pedido_estado CHECK (estado IN ('Pendiente','Pagado','Enviado','Entregado','Cancelado')),
    CONSTRAINT CK_Pedido_total  CHECK (total >= 0),
    CONSTRAINT FK_Pedido_Cliente FOREIGN KEY (id_cliente) REFERENCES Cliente (id_cliente),
    CONSTRAINT FK_Pedido_Direccion FOREIGN KEY (id_direccion, id_cliente)
        REFERENCES Direccion (id_direccion, id_cliente)
);

CREATE TABLE DetallePedido (
    id_pedido        INT           NOT NULL,
    id_producto      INT           NOT NULL,
    cantidad         INT           NOT NULL,
    precio_unitario  DECIMAL(12,2) NOT NULL,
    descuento        DECIMAL(12,2) NOT NULL CONSTRAINT DF_Detalle_descuento DEFAULT 0,
    CONSTRAINT PK_DetallePedido PRIMARY KEY (id_pedido, id_producto),
    CONSTRAINT CK_Detalle_cantidad  CHECK (cantidad > 0),
    CONSTRAINT CK_Detalle_precio    CHECK (precio_unitario > 0),
    CONSTRAINT CK_Detalle_descuento CHECK (descuento >= 0),
    CONSTRAINT FK_Detalle_Pedido   FOREIGN KEY (id_pedido)   REFERENCES Pedido (id_pedido),
    CONSTRAINT FK_Detalle_Producto FOREIGN KEY (id_producto) REFERENCES Producto (id_producto)
);

CREATE TABLE Pago (
    id_pago     INT IDENTITY(1,1) NOT NULL,
    id_pedido   INT           NOT NULL,
    fecha_pago  DATETIME2(0)  NOT NULL,
    metodo      VARCHAR(20)   NOT NULL,
    valor       DECIMAL(14,2) NOT NULL,
    estado      VARCHAR(12)   NOT NULL,
    CONSTRAINT PK_Pago PRIMARY KEY (id_pago),
    CONSTRAINT CK_Pago_metodo CHECK (metodo IN ('Tarjeta credito','Tarjeta debito','PSE','Nequi','Efectivo')),
    CONSTRAINT CK_Pago_estado CHECK (estado IN ('Aprobado','Rechazado')),
    CONSTRAINT CK_Pago_valor  CHECK (valor > 0),
    CONSTRAINT FK_Pago_Pedido FOREIGN KEY (id_pedido) REFERENCES Pedido (id_pedido)
);

CREATE TABLE Envio (
    id_envio        INT IDENTITY(1,1) NOT NULL,
    id_pedido       INT          NOT NULL,
    transportadora  VARCHAR(30)  NOT NULL,
    numero_guia     VARCHAR(20)  NOT NULL,
    fecha_envio     DATETIME2(0) NOT NULL,
    fecha_entrega   DATETIME2(0) NULL,
    estado          VARCHAR(15)  NOT NULL,
    CONSTRAINT PK_Envio PRIMARY KEY (id_envio),
    CONSTRAINT UQ_Envio_pedido UNIQUE (id_pedido),          -- 1 : 0..1 con Pedido
    CONSTRAINT UQ_Envio_guia   UNIQUE (numero_guia),
    CONSTRAINT CK_Envio_transportadora CHECK (transportadora IN ('Servientrega','Coordinadora','Interrapidisimo','Envia')),
    CONSTRAINT CK_Envio_estado CHECK (estado IN ('En transito','Entregado')),
    CONSTRAINT CK_Envio_fechas CHECK (fecha_entrega IS NULL OR fecha_entrega >= fecha_envio),
    CONSTRAINT FK_Envio_Pedido FOREIGN KEY (id_pedido) REFERENCES Pedido (id_pedido)
);

CREATE TABLE Resena (
    id_resena     INT IDENTITY(1,1) NOT NULL,
    id_producto   INT           NOT NULL,
    id_cliente    INT           NOT NULL,
    calificacion  TINYINT       NOT NULL,
    comentario    NVARCHAR(400) NULL,
    fecha         DATE          NOT NULL,
    CONSTRAINT PK_Resena PRIMARY KEY (id_resena),
    CONSTRAINT UQ_Resena_cliente_producto UNIQUE (id_cliente, id_producto),
    CONSTRAINT CK_Resena_calificacion CHECK (calificacion BETWEEN 1 AND 5),
    CONSTRAINT FK_Resena_Producto FOREIGN KEY (id_producto) REFERENCES Producto (id_producto),
    CONSTRAINT FK_Resena_Cliente  FOREIGN KEY (id_cliente)  REFERENCES Cliente (id_cliente)
);
GO

-- 6. Índices sobre las FK (SQL Server NO los crea solo)
CREATE INDEX IX_Producto_categoria ON Producto (id_categoria);
CREATE INDEX IX_Producto_proveedor ON Producto (id_proveedor);
CREATE INDEX IX_Direccion_cliente  ON Direccion (id_cliente);
CREATE INDEX IX_Pedido_cliente     ON Pedido (id_cliente);
CREATE INDEX IX_Detalle_producto   ON DetallePedido (id_producto);
CREATE INDEX IX_Pago_pedido        ON Pago (id_pedido);
CREATE INDEX IX_Resena_producto    ON Resena (id_producto);
GO

-- 7. Comprobación: debe listar las 10 tablas
SELECT TABLE_NAME
FROM INFORMATION_SCHEMA.TABLES
WHERE TABLE_TYPE = 'BASE TABLE'
ORDER BY TABLE_NAME;