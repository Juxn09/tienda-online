/* =========================================================
   Tienda en línea - Verificación de coherencia de los datos
   Cada fila cuenta violaciones de una regla: todas deben ser 0.
   ========================================================= */
USE TiendaOnline;
GO

SELECT regla, violaciones FROM (

    SELECT 1 AS n, 'Total del pedido distinto a la suma de sus detalles' AS regla,
           COUNT(*) AS violaciones
    FROM Pedido p
    JOIN (SELECT id_pedido, SUM(cantidad * precio_unitario - descuento) AS suma
          FROM DetallePedido GROUP BY id_pedido) d ON d.id_pedido = p.id_pedido
    WHERE p.total <> d.suma

    UNION ALL
    SELECT 2, 'Pedido sin detalles', COUNT(*)
    FROM Pedido p
    WHERE NOT EXISTS (SELECT 1 FROM DetallePedido d WHERE d.id_pedido = p.id_pedido)

    UNION ALL
    SELECT 3, 'Envio de un pedido no despachado', COUNT(*)
    FROM Envio e JOIN Pedido p ON p.id_pedido = e.id_pedido
    WHERE p.estado NOT IN ('Enviado', 'Entregado')

    UNION ALL
    SELECT 4, 'Pedido despachado sin envio', COUNT(*)
    FROM Pedido p
    WHERE p.estado IN ('Enviado', 'Entregado')
      AND NOT EXISTS (SELECT 1 FROM Envio e WHERE e.id_pedido = p.id_pedido)

    UNION ALL
    SELECT 5, 'Fecha de entrega no coincide con el estado', COUNT(*)
    FROM Envio e JOIN Pedido p ON p.id_pedido = e.id_pedido
    WHERE (p.estado = 'Entregado'  AND e.fecha_entrega IS NULL)
       OR (p.estado <> 'Entregado' AND e.fecha_entrega IS NOT NULL)

    UNION ALL
    SELECT 6, 'Pedido pagado sin exactamente 1 pago aprobado', COUNT(*)
    FROM Pedido p
    WHERE p.estado IN ('Pagado', 'Enviado', 'Entregado')
      AND (SELECT COUNT(*) FROM Pago pg
           WHERE pg.id_pedido = p.id_pedido AND pg.estado = 'Aprobado') <> 1

    UNION ALL
    SELECT 7, 'Pago aprobado por un valor distinto al total', COUNT(*)
    FROM Pago pg JOIN Pedido p ON p.id_pedido = pg.id_pedido
    WHERE pg.estado = 'Aprobado' AND pg.valor <> p.total

    UNION ALL
    SELECT 8, 'Pedido pendiente o cancelado con pago aprobado', COUNT(*)
    FROM Pago pg JOIN Pedido p ON p.id_pedido = pg.id_pedido
    WHERE pg.estado = 'Aprobado' AND p.estado IN ('Pendiente', 'Cancelado')

    UNION ALL
    SELECT 9, 'Resena de un producto que el cliente no recibio', COUNT(*)
    FROM Resena r
    WHERE NOT EXISTS (SELECT 1
                      FROM DetallePedido d
                      JOIN Pedido p ON p.id_pedido = d.id_pedido
                      WHERE p.id_cliente = r.id_cliente
                        AND d.id_producto = r.id_producto
                        AND p.estado = 'Entregado')

    UNION ALL
    SELECT 10, 'Pedido anterior al registro del cliente', COUNT(*)
    FROM Pedido p JOIN Cliente c ON c.id_cliente = p.id_cliente
    WHERE CAST(p.fecha_pedido AS DATE) < c.fecha_registro

    UNION ALL
    SELECT 11, 'Envio anterior a la fecha del pedido', COUNT(*)
    FROM Envio e JOIN Pedido p ON p.id_pedido = e.id_pedido
    WHERE e.fecha_envio < p.fecha_pedido

) AS v
ORDER BY n;

-- Distribución de estados (para ver que los datos son realistas)
SELECT estado, COUNT(*) AS pedidos
FROM Pedido
GROUP BY estado
ORDER BY pedidos DESC;