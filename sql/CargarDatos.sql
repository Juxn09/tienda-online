/* =========================================================
   Tienda en línea - Script de carga de datos
   Requisito: haber ejecutado CrearTablas.sql (tablas vacías).
   Para recargar desde cero: CrearTablas.sql y luego este.
   ========================================================= */
USE TiendaOnline;
GO

/* ---------------------------------------------------------
   Función auxiliar: número pseudoaleatorio REPRODUCIBLE.
   Devuelve un entero entre 0 y @maximo - 1.
   Misma semilla + misma etiqueta = mismo resultado siempre.
   --------------------------------------------------------- */
CREATE OR ALTER FUNCTION dbo.Azar (@semilla INT, @etiqueta VARCHAR(20), @maximo INT)
RETURNS INT
AS
BEGIN
    RETURN (CAST(SUBSTRING(HASHBYTES('MD5', CONCAT(@semilla, '-', @etiqueta)), 1, 4) AS INT)
            & 2147483647) % @maximo;
END;
GO

SET NOCOUNT ON;

-- Protección: si ya hay datos, se detiene (evita duplicar)
IF EXISTS (SELECT 1 FROM Categoria)
    THROW 50001, 'Las tablas ya tienen datos. Ejecute primero CrearTablas.sql y luego este script.', 1;

/* =========================================================
   1. CATEGORIA (10)
   ========================================================= */
INSERT INTO Categoria (nombre, descripcion) VALUES
(N'Tecnología',   N'Computadores, celulares y accesorios electrónicos'),
(N'Hogar',        N'Cocina, muebles y decoración'),
(N'Ropa',         N'Prendas de vestir para hombre y mujer'),
(N'Deportes',     N'Implementos y equipos deportivos'),
(N'Libros',       N'Libros impresos de diferentes géneros'),
(N'Juguetes',     N'Juguetes y juegos de mesa'),
(N'Belleza',      N'Cuidado personal y cosméticos'),
(N'Mascotas',     N'Alimento y accesorios para mascotas'),
(N'Herramientas', N'Herramientas manuales y eléctricas'),
(N'Papelería',    N'Útiles escolares y de oficina');

/* =========================================================
   2. PROVEEDOR (15)
   ========================================================= */
INSERT INTO Proveedor (nit, razon_social, ciudad, telefono, email) VALUES
('900100001', N'TecnoImport S.A.S.',            N'Bogotá',       '6015550101', 'ventas@tecnoimport.com.co'),
('900100002', N'Distribuidora Andina S.A.S.',   N'Medellín',     '6045550102', 'pedidos@andina.com.co'),
('900100003', N'Hogar Total Ltda.',             N'Cali',         '6025550103', 'contacto@hogartotal.com.co'),
('900100004', N'Textiles del Valle S.A.',       N'Cali',         '6025550104', 'ventas@textilesvalle.com.co'),
('900100005', N'Deportes Extremos S.A.S.',      N'Bogotá',       '6015550105', 'info@deportesextremos.com.co'),
('900100006', N'Editorial Horizonte S.A.',      N'Bogotá',       '6015550106', 'libros@horizonte.com.co'),
('900100007', N'Jugueterías Unidas S.A.S.',     N'Medellín',     '6045550107', 'ventas@juguetesunidas.com.co'),
('900100008', N'Belleza Natural S.A.S.',        N'Barranquilla', '6055550108', 'contacto@bellezanatural.com.co'),
('900100009', N'PetShop Mayorista S.A.S.',      N'Bucaramanga',  '6075550109', 'pedidos@petshop.com.co'),
('900100010', N'Ferretería Industrial S.A.',    N'Medellín',     '6045550110', 'ventas@ferreind.com.co'),
('900100011', N'Papelera Nacional S.A.',        N'Pereira',      '6065550111', 'ventas@papelera.com.co'),
('900100012', N'Mundo Digital S.A.S.',          N'Bogotá',       '6015550112', 'ventas@mundodigital.com.co'),
('900100013', N'Casa y Estilo S.A.S.',          N'Cartagena',    '6055550113', 'info@casayestilo.com.co'),
('900100014', N'Importadora del Caribe S.A.S.', N'Barranquilla', '6055550114', 'compras@impcaribe.com.co'),
('900100015', N'Logística Comercial S.A.S.',    N'Manizales',    '6065550115', 'ventas@logcomercial.com.co');

/* =========================================================
   3. PRODUCTO (300) = 50 productos base x 6 variantes
   ========================================================= */
DECLARE @Base TABLE (id INT IDENTITY(1,1), id_categoria INT, nombre NVARCHAR(80), precio DECIMAL(12,2));
INSERT INTO @Base (id_categoria, nombre, precio) VALUES
(1, N'Audífonos inalámbricos', 180000), (1, N'Mouse inalámbrico', 65000), (1, N'Teclado mecánico', 250000),
(1, N'Celular', 1200000), (1, N'Portátil', 2800000),
(2, N'Juego de sartenes', 220000), (2, N'Licuadora', 260000), (2, N'Lámpara de escritorio', 90000),
(2, N'Silla de oficina', 450000), (2, N'Juego de sábanas', 120000),
(3, N'Camiseta de algodón', 45000), (3, N'Jean clásico', 120000), (3, N'Chaqueta impermeable', 210000),
(3, N'Vestido casual', 150000), (3, N'Sudadera', 95000),
(4, N'Balón de fútbol', 85000), (4, N'Mancuernas 5 kg', 110000), (4, N'Tapete de yoga', 70000),
(4, N'Bicicleta estática', 950000), (4, N'Tenis para correr', 320000),
(5, N'Novela', 55000), (5, N'Libro de cocina', 75000), (5, N'Libro de programación', 130000),
(5, N'Cómic', 40000), (5, N'Enciclopedia infantil', 160000),
(6, N'Rompecabezas 1000 piezas', 60000), (6, N'Carro a control remoto', 150000), (6, N'Muñeca', 80000),
(6, N'Juego de mesa', 110000), (6, N'Bloques de construcción', 190000),
(7, N'Crema hidratante', 48000), (7, N'Perfume', 280000), (7, N'Secador de cabello', 170000),
(7, N'Kit de maquillaje', 130000), (7, N'Protector solar', 52000),
(8, N'Alimento para perro 15 kg', 190000), (8, N'Alimento para gato 7 kg', 120000), (8, N'Cama para mascota', 140000),
(8, N'Juguete para perro', 30000), (8, N'Arena para gato', 45000),
(9, N'Taladro percutor', 320000), (9, N'Juego de destornilladores', 65000), (9, N'Caja de herramientas', 150000),
(9, N'Sierra circular', 480000), (9, N'Cinta métrica', 25000),
(10, N'Cuaderno argollado', 15000), (10, N'Caja de colores', 28000), (10, N'Agenda', 45000),
(10, N'Calculadora científica', 85000), (10, N'Morral escolar', 130000);

DECLARE @Variante TABLE (id INT, nombre NVARCHAR(10), factor DECIMAL(4,2));
INSERT INTO @Variante VALUES
(1, N'Lite', 0.80), (2, N'Básico', 1.00), (3, N'Eco', 1.10),
(4, N'Plus', 1.30), (5, N'Pro', 1.60), (6, N'Max', 2.00);

INSERT INTO Producto (sku, nombre, descripcion, precio, stock, activo, id_categoria, id_proveedor)
SELECT
    CONCAT('SKU-', RIGHT(CONCAT('0000', b.id * 10 + v.id), 4)),
    CONCAT(b.nombre, N' ', v.nombre),
    CONCAT(b.nombre, N' versión ', v.nombre),
    CAST(ROUND(b.precio * v.factor, -2) AS DECIMAL(12,2)),
    dbo.Azar(b.id * 10 + v.id, 'stock', 200),
    CASE WHEN dbo.Azar(b.id * 10 + v.id, 'activo', 20) = 0 THEN 0 ELSE 1 END,
    b.id_categoria,
    -- 70 %: proveedor especialista de la categoría; 30 %: distribuidor general
    CASE WHEN dbo.Azar(b.id * 10 + v.id, 'prov', 10) < 7
         THEN CHOOSE(b.id_categoria, 1, 3, 4, 5, 6, 7, 8, 9, 10, 11)
         ELSE CHOOSE(dbo.Azar(b.id * 10 + v.id, 'gen', 5) + 1, 2, 12, 13, 14, 15)
    END
FROM @Base b
CROSS JOIN @Variante v
ORDER BY b.id, v.id;

/* =========================================================
   4. CLIENTE (800)
   ========================================================= */
DECLARE @Nombre TABLE (id INT IDENTITY(1,1), nombre NVARCHAR(30));
INSERT INTO @Nombre (nombre) VALUES
(N'Juan'), (N'María'), (N'Carlos'), (N'Ana'), (N'Luis'), (N'Laura'), (N'Andrés'), (N'Valentina'),
(N'Jorge'), (N'Camila'), (N'Diego'), (N'Daniela'), (N'Felipe'), (N'Sofía'), (N'Santiago'), (N'Natalia'),
(N'Sebastián'), (N'Paula'), (N'Alejandro'), (N'Carolina'), (N'David'), (N'Juliana'), (N'Miguel'),
(N'Isabella'), (N'Ricardo'), (N'Andrea'), (N'Óscar'), (N'Mariana'), (N'Esteban'), (N'Lucía');

DECLARE @Apellido TABLE (id INT IDENTITY(1,1), apellido NVARCHAR(30));
INSERT INTO @Apellido (apellido) VALUES
(N'Gómez'), (N'Rodríguez'), (N'Martínez'), (N'García'), (N'López'), (N'Hernández'), (N'González'),
(N'Pérez'), (N'Sánchez'), (N'Ramírez'), (N'Torres'), (N'Díaz'), (N'Vargas'), (N'Moreno'), (N'Rojas'),
(N'Castro'), (N'Ortiz'), (N'Muñoz'), (N'Jiménez'), (N'Suárez'), (N'Romero'), (N'Herrera'), (N'Medina'),
(N'Aguilar'), (N'Castillo'), (N'Restrepo'), (N'Cárdenas'), (N'Ospina'), (N'Salazar'), (N'Zapata');

INSERT INTO Cliente (documento, nombres, apellidos, email, telefono, fecha_registro)
SELECT
    CAST(1000000000 + s.value * 7919 AS VARCHAR(15)),
    n.nombre,
    CONCAT(a1.apellido, N' ', a2.apellido),
    -- correo sin tildes: maria.gomez25@correo.com
    LOWER(TRANSLATE(CONCAT(n.nombre, '.', a1.apellido, s.value, '@correo.com'),
                    N'áéíóúñÁÉÍÓÚÑ', N'aeiounAEIOUN')),
    CONCAT('3', 100000000 + dbo.Azar(s.value, 'tel', 899999999)),
    DATEADD(DAY, dbo.Azar(s.value, 'registro', 900), CAST('2023-01-01' AS DATE))
FROM GENERATE_SERIES(1, 800) AS s
JOIN @Nombre   n  ON n.id  = dbo.Azar(s.value, 'nombre', 30) + 1
JOIN @Apellido a1 ON a1.id = dbo.Azar(s.value, 'ape1', 30) + 1
JOIN @Apellido a2 ON a2.id = dbo.Azar(s.value, 'ape2', 30) + 1
ORDER BY s.value;

/* =========================================================
   5. DIRECCION (1.000)
      - 800 "Casa" (principal): id_direccion = id_cliente
      - 200 "Oficina" para los clientes 4, 8, 12... 800:
        id_direccion = 800 + id_cliente / 4
   ========================================================= */
DECLARE @Ciudad TABLE (id INT, ciudad NVARCHAR(60), departamento NVARCHAR(60));
INSERT INTO @Ciudad VALUES
(1, N'Bogotá', N'Bogotá D.C.'), (2, N'Medellín', N'Antioquia'), (3, N'Cali', N'Valle del Cauca'),
(4, N'Barranquilla', N'Atlántico'), (5, N'Cartagena', N'Bolívar'), (6, N'Bucaramanga', N'Santander'),
(7, N'Pereira', N'Risaralda'), (8, N'Manizales', N'Caldas'), (9, N'Santa Marta', N'Magdalena'),
(10, N'Cúcuta', N'Norte de Santander'), (11, N'Ibagué', N'Tolima'), (12, N'Villavicencio', N'Meta');

INSERT INTO Direccion (id_cliente, alias, direccion, ciudad, departamento, es_principal)
SELECT
    s.value,
    N'Casa',
    CONCAT(CHOOSE(dbo.Azar(s.value, 'via', 3) + 1, N'Calle', N'Carrera', N'Avenida'), N' ',
           dbo.Azar(s.value, 'n1', 120) + 1, N' # ', dbo.Azar(s.value, 'n2', 90) + 1,
           N' - ', dbo.Azar(s.value, 'n3', 99) + 1),
    c.ciudad,
    c.departamento,
    1
FROM GENERATE_SERIES(1, 800) AS s
-- 30 % Bogotá, el resto repartido entre las 12 ciudades
JOIN @Ciudad c ON c.id = CASE WHEN dbo.Azar(s.value, 'bog', 10) < 3 THEN 1
                              ELSE dbo.Azar(s.value, 'ciudad', 12) + 1 END
ORDER BY s.value;

INSERT INTO Direccion (id_cliente, alias, direccion, ciudad, departamento, es_principal)
SELECT
    s.value * 4,
    N'Oficina',
    CONCAT(N'Carrera ', dbo.Azar(s.value, 'of1', 80) + 1, N' # ', dbo.Azar(s.value, 'of2', 120) + 1,
           N' - ', dbo.Azar(s.value, 'of3', 99) + 1, N' Oficina ', dbo.Azar(s.value, 'of4', 900) + 100),
    casa.ciudad,          -- la oficina queda en la misma ciudad de la casa
    casa.departamento,
    0
FROM GENERATE_SERIES(1, 200) AS s
JOIN Direccion casa ON casa.id_direccion = s.value * 4
ORDER BY s.value;

/* =========================================================
   6. PEDIDO (2.000) entre 2025-07-01 y 2026-10-10
      - Clientes con distribución desigual (unos compran mucho)
      - Pedidos antiguos: Entregado (96 %) o Cancelado (4 %)
      - Pedidos desde 2026-09-25: todos los estados
   ========================================================= */
WITH base AS (
    SELECT
        s.value AS n,
        1 + (dbo.Azar(s.value, 'cli1', 800) * dbo.Azar(s.value, 'cli2', 800)) / 800 AS id_cliente,
        DATEADD(MINUTE, dbo.Azar(s.value, 'fecha', 466 * 1440),
                CAST('2025-07-01' AS DATETIME2(0))) AS fecha_pedido
    FROM GENERATE_SERIES(1, 2000) AS s
),
ped AS (
    SELECT
        n, id_cliente, fecha_pedido,
        -- clientes con oficina la usan 1 de cada 3 veces
        CASE WHEN id_cliente % 4 = 0 AND dbo.Azar(n, 'dir', 3) = 0
             THEN 800 + id_cliente / 4
             ELSE id_cliente END AS id_direccion,
        dbo.Azar(n, 'estado', 100) AS x
    FROM base
)
INSERT INTO Pedido (id_cliente, id_direccion, fecha_pedido, estado)
SELECT
    id_cliente,
    id_direccion,
    fecha_pedido,
    CASE
        WHEN fecha_pedido < '2026-09-25' THEN
             CASE WHEN x < 4 THEN 'Cancelado' ELSE 'Entregado' END
        ELSE CASE WHEN x < 5  THEN 'Cancelado'
                  WHEN x < 25 THEN 'Pendiente'
                  WHEN x < 45 THEN 'Pagado'
                  WHEN x < 75 THEN 'Enviado'
                  ELSE 'Entregado' END
    END
FROM ped
ORDER BY fecha_pedido;      -- así id_pedido sigue el orden cronológico

/* =========================================================
   7. DETALLEPEDIDO (~5.200): de 1 a 5 productos distintos por pedido
   ========================================================= */
WITH ped AS (
    SELECT
        id_pedido,
        CASE dbo.Azar(id_pedido, 'items', 10)
            WHEN 0 THEN 1 WHEN 1 THEN 1
            WHEN 2 THEN 2 WHEN 3 THEN 2 WHEN 4 THEN 2
            WHEN 5 THEN 3 WHEN 6 THEN 3 WHEN 7 THEN 3
            WHEN 8 THEN 4 ELSE 5 END AS k,
        -- producto base con distribución desigual (unos se venden mucho más)
        (dbo.Azar(id_pedido, 'b1', 300) * dbo.Azar(id_pedido, 'b2', 300)) / 300 AS base,
        1 + dbo.Azar(id_pedido, 'paso', 59) AS paso
    FROM Pedido
),
items AS (
    -- base*7 reparte los productos populares entre categorías;
    -- el "paso" garantiza productos distintos dentro del mismo pedido
    SELECT p.id_pedido, g.value AS i,
           ((p.base * 7 + g.value * p.paso) % 300) + 1 AS id_producto
    FROM ped p
    CROSS APPLY GENERATE_SERIES(1, p.k) AS g
),
lineas AS (
    SELECT
        it.id_pedido,
        it.id_producto,
        CASE WHEN dbo.Azar(it.id_pedido * 10 + it.i, 'cant', 10) < 6 THEN 1
             WHEN dbo.Azar(it.id_pedido * 10 + it.i, 'cant', 10) < 9 THEN 2
             ELSE 3 END AS cantidad,
        -- precio histórico: entre el 90 % y el 100 % del precio actual
        CAST(ROUND(pr.precio * (0.90 + dbo.Azar(it.id_pedido * 10 + it.i, 'hist', 11) / 100.0), -2)
             AS DECIMAL(12,2)) AS precio_unitario,
        dbo.Azar(it.id_pedido * 10 + it.i, 'desc', 10) AS d
    FROM items it
    JOIN Producto pr ON pr.id_producto = it.id_producto
)
INSERT INTO DetallePedido (id_pedido, id_producto, cantidad, precio_unitario, descuento)
SELECT
    id_pedido, id_producto, cantidad, precio_unitario,
    CAST(CASE d WHEN 0 THEN ROUND(cantidad * precio_unitario * 0.10, -2)   -- 10 % de las líneas: 10 % dcto
                WHEN 1 THEN ROUND(cantidad * precio_unitario * 0.05, -2)   -- 10 % de las líneas: 5 % dcto
                ELSE 0 END AS DECIMAL(12,2))
FROM lineas;

/* =========================================================
   8. TOTAL del pedido = suma de sus líneas
   ========================================================= */
UPDATE p
SET total = t.suma
FROM Pedido p
JOIN (SELECT id_pedido, SUM(cantidad * precio_unitario - descuento) AS suma
      FROM DetallePedido
      GROUP BY id_pedido) t ON t.id_pedido = p.id_pedido;

/* =========================================================
   9. PAGO (~2.200)
      - Pagado/Enviado/Entregado: 1 pago Aprobado por el total
        (+10 % con un intento Rechazado antes)
      - Cancelado: 1 pago Rechazado
      - Pendiente: sin pagos
   ========================================================= */
INSERT INTO Pago (id_pedido, fecha_pago, metodo, valor, estado)
SELECT id_pedido, fecha_pago, metodo, valor, estado
FROM (
    SELECT id_pedido,
           DATEADD(MINUTE, 5, fecha_pedido) AS fecha_pago,
           CHOOSE(dbo.Azar(id_pedido, 'met1', 5) + 1,
                  'Tarjeta credito', 'Tarjeta debito', 'PSE', 'Nequi', 'Efectivo') AS metodo,
           total AS valor,
           'Rechazado' AS estado
    FROM Pedido
    WHERE estado = 'Cancelado'
       OR (estado IN ('Pagado', 'Enviado', 'Entregado') AND dbo.Azar(id_pedido, 'rechazo', 10) = 0)

    UNION ALL

    SELECT id_pedido,
           DATEADD(MINUTE, 30 + dbo.Azar(id_pedido, 'tpago', 120), fecha_pedido),
           CHOOSE(dbo.Azar(id_pedido, 'met2', 5) + 1,
                  'Tarjeta credito', 'Tarjeta debito', 'PSE', 'Nequi', 'Efectivo'),
           total,
           'Aprobado'
    FROM Pedido
    WHERE estado IN ('Pagado', 'Enviado', 'Entregado')
) AS pagos
ORDER BY fecha_pago;

/* =========================================================
   10. ENVIO (~1.900): solo pedidos Enviados o Entregados
   ========================================================= */
INSERT INTO Envio (id_pedido, transportadora, numero_guia, fecha_envio, fecha_entrega, estado)
SELECT
    id_pedido,
    transportadora,
    CONCAT(UPPER(LEFT(transportadora, 3)), RIGHT(CONCAT('0000000', id_pedido), 7)),
    fecha_envio,
    CASE WHEN estado = 'Entregado'
         THEN DATEADD(HOUR, 24 + dbo.Azar(id_pedido, 'tentrega', 120), fecha_envio) END,
    CASE WHEN estado = 'Entregado' THEN 'Entregado' ELSE 'En transito' END
FROM (
    SELECT id_pedido, estado,
           CHOOSE(dbo.Azar(id_pedido, 'transp', 4) + 1,
                  'Servientrega', 'Coordinadora', 'Interrapidisimo', 'Envia') AS transportadora,
           DATEADD(HOUR, 24 + dbo.Azar(id_pedido, 'tenvio', 48), fecha_pedido) AS fecha_envio
    FROM Pedido
    WHERE estado IN ('Enviado', 'Entregado')
) AS e
ORDER BY id_pedido;

/* =========================================================
   11. RESENA (1.200): solo de productos que el cliente
       recibió (pedido Entregado), una por cliente-producto.
       La calidad depende del proveedor (unos son peores).
   ========================================================= */
WITH compras AS (
    SELECT p.id_cliente, d.id_producto, MIN(e.fecha_entrega) AS primera_entrega
    FROM DetallePedido d
    JOIN Pedido p ON p.id_pedido = d.id_pedido
    JOIN Envio  e ON e.id_pedido = p.id_pedido
    WHERE p.estado = 'Entregado'
    GROUP BY p.id_cliente, d.id_producto
),
elegidas AS (
    SELECT TOP (1200) c.*, pr.id_proveedor,
           c.id_cliente * 1000 + c.id_producto AS semilla
    FROM compras c
    JOIN Producto pr ON pr.id_producto = c.id_producto
    ORDER BY dbo.Azar(c.id_cliente * 1000 + c.id_producto, 'resena', 1000000), c.id_cliente, c.id_producto
),
calificadas AS (
    SELECT *,
           -- base del proveedor (2, 3 o 4) + ruido (-1, 0 o +1)  => 1 a 5
           2 + dbo.Azar(id_proveedor, 'calidad', 3) + dbo.Azar(semilla, 'ruido', 3) - 1 AS calificacion
    FROM elegidas
)
INSERT INTO Resena (id_producto, id_cliente, calificacion, comentario, fecha)
SELECT
    id_producto,
    id_cliente,
    calificacion,
    CHOOSE(calificacion,
           N'Muy malo, no lo recomiendo',
           N'Regular, esperaba más',
           N'Cumple, nada especial',
           N'Buen producto, llegó bien',
           N'Excelente, lo recomiendo'),
    CAST(DATEADD(DAY, 1 + dbo.Azar(semilla, 'fresena', 20), primera_entrega) AS DATE)
FROM calificadas
ORDER BY 5;   -- por fecha
GO

/* =========================================================
   12. Limpieza y conteo final
   ========================================================= */
DROP FUNCTION IF EXISTS dbo.Azar;
GO

SELECT tabla, registros FROM (
    SELECT 'Categoria' AS tabla, COUNT(*) AS registros, 1 AS orden FROM Categoria UNION ALL
    SELECT 'Proveedor',     COUNT(*), 2  FROM Proveedor     UNION ALL
    SELECT 'Producto',      COUNT(*), 3  FROM Producto      UNION ALL
    SELECT 'Cliente',       COUNT(*), 4  FROM Cliente       UNION ALL
    SELECT 'Direccion',     COUNT(*), 5  FROM Direccion     UNION ALL
    SELECT 'Pedido',        COUNT(*), 6  FROM Pedido        UNION ALL
    SELECT 'DetallePedido', COUNT(*), 7  FROM DetallePedido UNION ALL
    SELECT 'Pago',          COUNT(*), 8  FROM Pago          UNION ALL
    SELECT 'Envio',         COUNT(*), 9  FROM Envio         UNION ALL
    SELECT 'Resena',        COUNT(*), 10 FROM Resena
) AS t
ORDER BY orden;