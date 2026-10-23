# Verificación de la migración

Script: `migracion/Verificar.py` · Resultado completo: `evidencias/F5VerificacionMigracion.txt`

**Resultado: 25 de 25 verificaciones correctas.**

## 1. Coherencia de los datos en SQL Server (antes de migrar)

Antes de migrar se comprobó que los datos de origen cumplen las reglas de negocio con `sql/VerificarCoherencia.sql`: 11 consultas que buscan violaciones (por ejemplo, pedidos despachados sin envío o totales que no coinciden con sus detalles). Todas devolvieron 0 violaciones.

## 2. Cómo se unieron las tablas

| Tablas de SQL Server | Documento en MongoDB | Cómo se hizo en `Migrar.py` |
|---|---|---|
| Pedido + DetallePedido + Pago + Envio + (copia de) Direccion | `pedidos` | Cada tabla hija se leyó una sola vez y se agrupó en memoria por `id_pedido` (función `agrupar`). Luego, a cada pedido se le asignaron sus detalles como `items[]`, sus pagos como `pagos[]`, su envío como `envio` (o `null`) y una copia de su dirección como `direccionEnvio`. |
| Cliente + Direccion | `clientes` | Las direcciones se agruparon por `id_cliente` y se embebieron como `direcciones[]`. |

Dentro de cada elemento embebido se conservó el identificador original (`idPago`, `idEnvio`, `idDireccion`) y el `_id` de cada documento es el mismo id de SQL Server, para poder comparar registro a registro.

## 3. Cómo se comprobó que no se perdió información

La verificación compara SQL Server contra MongoDB en cinco capas. Cada capa detecta un tipo de error distinto.

### Capa 1 – Conteos

| SQL Server | MongoDB | SQL | MongoDB |
|---|---|---|---|
| Categoria, Proveedor, Producto, Cliente, Pedido, Resena | documentos de cada colección | 10 / 15 / 300 / 800 / 2.000 / 1.200 | iguales |
| `COUNT(*)` DetallePedido | suma del tamaño de todos los `items` | 5.190 | 5.190 |
| `COUNT(*)` Pago | suma del tamaño de todos los `pagos` | 2.184 | 2.184 |
| `COUNT(*)` Direccion | suma del tamaño de todas las `direcciones` | 1.000 | 1.000 |
| `COUNT(*)` Envio | pedidos con `envio` distinto de `null` | 1.896 | 1.896 |

Las tablas que se embebieron no desaparecen: sus filas se cuentan como elementos de los arrays con `$group` y `$sum: { $size: "$items" }`.

### Capa 2 – Referencias

Para cada referencia (`pedidos.clienteId`, `pedidos.items.productoId`, `productos.categoriaId`, `productos.proveedorId`, `resenas.productoId`, `resenas.clienteId`) se hizo un `$lookup` hacia la colección destino y se contaron los documentos sin pareja (`$match: { encontrado: { $size: 0 } }`). Resultado: **0 referencias rotas**.

### Capa 3 – Estructuras embebidas

- Pedido por pedido, la cantidad de `items` y de `pagos` coincide con la cantidad de filas en SQL Server (0 diferencias). Esto descarta que un detalle haya quedado en el pedido equivocado, algo que el conteo total no detectaría.
- Todo pedido Enviado o Entregado tiene `envio`, y ningún otro lo tiene (0 incoherencias).
- Ningún pedido quedó sin items; todos los totales son `Decimal128`.

### Capa 4 – Contenido

| Comparación | SQL Server | MongoDB |
|---|---|---|
| Suma de totales de pedidos | $2.212.003.800,00 | $2.212.003.800,00 |
| Suma de pagos aprobados | $2.137.413.000,00 | $2.137.413.000,00 |
| Pedidos cuyo total no es la suma de sus items (calculado en MongoDB con `$map`) | 0 | 0 |

### Capa 5 – Datos puntuales

Se compararon 22 pedidos de muestra campo por campo (cliente, dirección, fecha, estado, total, cada item con su cantidad, precio y descuento, y número de guía del envío). Resultado: **0 diferencias**.

## 4. Prueba negativa

Para demostrar que la verificación detecta errores, se eliminó a propósito el último item del pedido 150 en MongoDB:

    db.pedidos.updateOne({ _id: 150 }, { $pop: { items: 1 } })

Al volver a verificar, el resultado bajó a **21 de 25**. Cuatro capas detectaron el error de forma independiente:

- Conteos: DetallePedido 5.190 en SQL frente a 5.189 en MongoDB.
- Estructuras: 1 pedido con distinta cantidad de items.
- Contenido: 1 pedido cuyo total no coincide con la suma de sus items.
- Puntuales: diferencia en el pedido 150.

Luego se ejecutó de nuevo la migración (que es repetible porque borra y recarga cada colección) y la verificación volvió a **25 de 25**. Evidencias: `F5PruebaNegativaDano.png`, `F5PruebaNegativaFallas.png` y `F5PruebaNegativaReparada.png`.