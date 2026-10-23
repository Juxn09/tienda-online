# Consultas de negocio – Aggregation Pipeline (MongoDB)

Base de datos: `TiendaOnline` · Los pipelines completos y comentados están en la carpeta `consultas/` y las capturas de los resultados en `evidencias/`.

Se consideran **ventas efectivas** los pedidos en estado Pagado, Enviado o Entregado (los Pendientes y Cancelados no son ventas reales).

## Resumen

| # | Pregunta de negocio | Decisión que apoya | Archivo |
|---|---|---|---|
| 1 | ¿Cuáles son los 10 productos más vendidos y de qué categoría son? | Reposición de inventario | `Consulta1ProductosMasVendidos.js` |
| 2 | ¿Cuánto vende cada categoría y qué % del total representa? | Presupuesto de marketing | `Consulta2VentasPorCategoria.js` |
| 3 | ¿Cómo evolucionan las ventas mes a mes? | Planeación por temporadas | `Consulta3VentasMensuales.js` |
| 4 | ¿Quiénes son los 10 mejores clientes y de qué ciudad son? | Programa de fidelización | `Consulta4MejoresClientes.js` |
| 5 | ¿Qué proveedores tienen peor calificación? | Renegociar o cambiar proveedores | `Consulta5ProveedoresPeorCalificados.js` |
| 6 | ¿Qué transportadora entrega más rápido? | Elección de transportadora y SLA | `Consulta6Transportadoras.js` |
| 7 | ¿Qué método de pago tiene más rechazos? | Revisión de la pasarela de pagos | `Consulta7RechazosPorMetodoPago.js` |

## Operadores utilizados

| Operador | Consultas |
|---|---|
| `$match` | 1, 2, 3, 4, 5 (como HAVING), 6 |
| `$project` | Todas |
| `$group` | Todas (dos veces en la 2) |
| `$sort` | Todas |
| `$limit` | 1, 4, 5 |
| `$unwind` | 1, 2, 4, 5, 7 |
| `$lookup` | 1, 2, 4, 5 |
| **Múltiples `$lookup`** | 1 y 2 (pedidos → productos → categorias), 5 (resenas → productos → proveedores) |
| Otros | `$setWindowFields` (2), `$dateToString` (3), `$filter` y `$addFields` (4), `$cond` (5, 6, 7), `$dateDiff` (6) |

---

## Consulta 1 – Productos más vendidos

- **Qué busca:** los 10 productos con más unidades vendidas, con su categoría, ingresos y stock actual.
- **Por qué importa:** los productos de mayor rotación no pueden agotarse; cada quiebre de stock es una venta perdida.
- **Decisión que apoya:** priorizar la reposición de estos productos y negociar compras por volumen con sus proveedores.
- **Impacto:** menos quiebres de inventario y compras enfocadas en lo que realmente se vende.
- **Etapas:** `$match` (ventas efectivas) → `$unwind` (items) → `$group` (por producto) → `$sort` → `$limit` 10 → `$lookup` productos → `$lookup` categorias → `$project`. El `$limit` va antes de los `$lookup` para unir solo 10 documentos y no 300.

**Resultado (top 3):**

| Producto | Categoría | Unidades | Pedidos | Ingresos | Stock |
|---|---|---|---|---|---|
| Vestido casual Lite | Ropa | 49 | 30 | $5.456.700 | 35 |
| Carro a control remoto Eco | Juguetes | 43 | 28 | $6.456.000 | 146 |
| Silla de oficina Lite | Hogar | 40 | 22 | $13.626.700 | 176 |

**Interpretación:** más unidades no implica más ingresos (la Silla de oficina vende menos unidades que el Vestido pero genera 2,5 veces sus ingresos). Las variantes económicas (Lite, Eco) son las que más rotan. Con unos 15 meses de datos, el Vestido vende ~3,3 unidades al mes y su stock cubre ~10 meses: no hay urgencia, pero es el primero a vigilar.

---

## Consulta 2 – Ventas por categoría

- **Qué busca:** ingresos, unidades y productos vendidos por categoría, y el porcentaje que representa cada una sobre el total.
- **Por qué importa:** muestra de dónde proviene el ingreso del negocio.
- **Decisión que apoya:** distribución del presupuesto de marketing y del espacio en el catálogo.
- **Impacto:** inversión alineada con el peso real de cada categoría.
- **Etapas:** `$match` → `$unwind` → `$group` por producto → `$lookup` productos → `$group` por categoría → `$lookup` categorias → `$setWindowFields` (total general) → `$project` (porcentaje) → `$sort`. Se agrupa dos veces para hacer el `$lookup` sobre 300 productos y no sobre ~5.000 items.

**Resultado (top 4):**

| Categoría | Ingresos | % del total | Unidades |
|---|---|---|---|
| Tecnología | $856.268.900 | 40,06 % | 689 |
| Deportes | $302.705.700 | 14,16 % | 802 |
| Hogar | $229.615.000 | 10,74 % | 831 |
| Herramientas | $168.841.900 | 7,90 % | 651 |

**Interpretación:** Tecnología aporta el 40 % de los ingresos con menos unidades que Hogar o Deportes. Existe una dependencia de una sola categoría; conviene fortalecer Deportes y Hogar, que ya tienen alto volumen de unidades, para diversificar. Las 10 categorías vendieron sus 30 productos: no hay productos sin movimiento.

---

## Consulta 3 – Ventas mensuales

- **Qué busca:** pedidos, ventas y ticket promedio de cada mes.
- **Por qué importa:** muestra la tendencia del negocio en el tiempo.
- **Decisión que apoya:** planeación de inventario, personal y campañas por temporada.
- **Impacto:** evitar falta de stock en meses fuertes y exceso en meses débiles.
- **Etapas:** `$match` → `$group` por mes (`$dateToString` con formato `%Y-%m`) → `$sort` cronológico → `$project`. No requiere `$unwind` porque usa el `total` almacenado en cada pedido.

**Resultado (primeros meses):**

| Mes | Pedidos | Ventas | Ticket promedio |
|---|---|---|---|
| 2025-07 | 122 | $129.100.200 | $1.058.198 |
| 2025-08 | 137 | $174.745.500 | $1.275.515 |
| 2025-09 | 120 | $130.270.800 | $1.085.590 |
| 2025-10 | 123 | $115.173.500 | $936.370 |
| 2025-11 | 144 | $158.601.400 | $1.101.399 |

**Interpretación:** el número de pedidos es estable (120–144 al mes), pero las ventas varían entre $115 M y $175 M por el ticket promedio: lo que mueve el ingreso es qué se compra, no cuántos compran. En meses de ticket bajo conviene impulsar el valor del carrito (combos, envío gratis desde cierto monto). Nota: los datos de prueba tienen fechas distribuidas uniformemente, por lo que no muestran temporadas reales; octubre de 2026 es un mes parcial.

---

## Consulta 4 – Mejores clientes

- **Qué busca:** los 10 clientes que más dinero han gastado, con su número de pedidos, ticket promedio, última compra y ciudad.
- **Por qué importa:** pocos clientes suelen concentrar una parte importante del ingreso.
- **Decisión que apoya:** programa de fidelización diferenciado.
- **Impacto:** retener clientes valiosos cuesta menos que conseguir nuevos.
- **Etapas:** `$match` → `$group` por cliente (incluye `$max` de la fecha) → `$sort` → `$limit` 10 → `$lookup` clientes → `$addFields` con `$filter` sobre el array embebido `direcciones` para obtener la principal → `$project`. La ciudad sale del cliente sin otro `$lookup` gracias al embebido.

**Resultado (top 3):**

| Cliente | Ciudad | Pedidos | Total comprado | Ticket promedio | Última compra |
|---|---|---|---|---|---|
| Felipe López Muñoz | Bogotá | 8 | $27.037.500 | $3.379.688 | 2026-09-25 |
| Andrés López González | Bogotá | 3 | $26.160.100 | $8.720.033 | 2026-09-02 |
| Lucía Torres Romero | Bogotá | 3 | $23.618.200 | $7.872.733 | 2025-12-23 |

**Interpretación:** comprar muchas veces no es lo mismo que gastar mucho. Hay clientes frecuentes (Felipe) y de alto ticket (Andrés, Lucía), que requieren estrategias distintas. Según el análisis RFM (Recencia, Frecuencia, Monto), Lucía no compra desde diciembre de 2025: es un cliente valioso en riesgo de pérdida y debe recibir una oferta de reactivación.

---

## Consulta 5 – Proveedores con peor calificación

- **Qué busca:** los 5 proveedores con menor calificación promedio, con su número de reseñas y el porcentaje de reseñas negativas (1 o 2 estrellas).
- **Por qué importa:** la mala calidad genera quejas, devoluciones y pérdida de clientes.
- **Decisión que apoya:** renegociar condiciones de calidad o reemplazar proveedores.
- **Impacto:** mayor satisfacción del cliente y protección de la reputación.
- **Etapas:** parte de la colección `resenas` → `$lookup` productos → `$group` por proveedor (con `$cond` para contar negativas) → `$match` de al menos 20 reseñas (equivalente a HAVING, para que el promedio sea confiable) → `$lookup` proveedores → `$project` → `$sort` ascendente → `$limit` 5.

**Resultado (4 peores):**

| Proveedor | Ciudad | Reseñas | Promedio | % negativas |
|---|---|---|---|---|
| Deportes Extremos S.A.S. | Bogotá | 101 | 1,79 | 73,3 % |
| Textiles del Valle S.A. | Cali | 87 | 1,83 | 74,7 % |
| Belleza Natural S.A.S. | Barranquilla | 107 | 1,85 | 70,1 % |
| PetShop Mayorista S.A.S. | Bucaramanga | 79 | 1,95 | 70,9 % |

**Interpretación:** cerca del 70 % de las reseñas de estos proveedores son negativas, con muestras de 79 a 107 reseñas. Cruzando con la consulta 2, Deportes Extremos abastece Deportes, la segunda categoría en ingresos: es la prioridad de renegociación. Cruzando con la consulta 1, Textiles del Valle surte Ropa, donde está el producto más vendido.

---

## Consulta 6 – Desempeño de transportadoras

- **Qué busca:** por transportadora, envíos entregados, días promedio y máximo de entrega, porcentaje de entregas tardías (más de 4 días) y días que tarda la tienda en despachar.
- **Por qué importa:** la demora en la entrega es una causa principal de quejas.
- **Decisión que apoya:** elección de transportadora y condiciones del contrato.
- **Impacto:** entregas más rápidas y menos reclamos.
- **Etapas:** `$match` sobre el subdocumento embebido `envio` → `$project` con `$dateDiff` (horas de despacho y de entrega) → `$group` por transportadora (con `$cond` para tardíos) → `$project` (horas a días) → `$sort`. No requiere `$lookup` porque el envío está embebido en el pedido.

**Resultado:**

| Transportadora | Envíos | Días entrega (prom.) | % tardíos | Días despacho tienda |
|---|---|---|---|---|
| Interrapidisimo | 483 | 3,38 | 36,2 % | 1,99 |
| Servientrega | 461 | 3,42 | 37,3 % | 2,02 |
| Coordinadora | 476 | 3,43 | 37,2 % | 2,00 |

**Interpretación:** las transportadoras están prácticamente empatadas (diferencias de ~1 hora), así que la elección debe hacerse por precio y cobertura. El ~37 % de entregas tardías es común a todas y se aborda con un acuerdo de nivel de servicio (SLA). El hallazgo principal es interno: la tienda tarda ~2 días en despachar, casi el 40 % del tiempo total de espera del cliente; reducir ese tiempo es la mejora con mayor impacto.

---

## Consulta 7 – Rechazos por método de pago

- **Qué busca:** por método de pago, intentos, rechazos, tasa de rechazo y valor rechazado frente al aprobado.
- **Por qué importa:** cada pago rechazado es una venta en riesgo; los pedidos Cancelados son los que no se recuperaron.
- **Decisión que apoya:** revisión de la pasarela, orden de los métodos en la página de pago y negociación con bancos.
- **Impacto:** menos ventas perdidas en el último paso de la compra.
- **Etapas:** `$unwind` del array embebido `pagos` → `$group` por método (con `$cond` para contar rechazos y sumar valores) → `$project` (tasa) → `$sort`.

**Resultado (principales):**

| Método | Intentos | Rechazados | Tasa de rechazo | Valor rechazado |
|---|---|---|---|---|
| Nequi | 447 | 69 | 15,4 % | $81.330.500 |
| Tarjeta crédito | 416 | 53 | 12,7 % | $64.712.600 |
| PSE | 417 | 52 | 12,5 % | $80.175.000 |

**Interpretación:** Nequi tiene la mayor tasa de rechazo y el mayor valor rechazado. Sin embargo, con ~430 intentos por método la diferencia (~3 puntos, unos 2 errores estándar) está en el límite de la significancia estadística, por lo que se recomienda monitorear antes de tomar medidas. Todos los métodos rechazan entre 11 % y 15 % de los intentos, lo que indica además un problema general de la pasarela. El total de rechazos (≈ 268) coincide con los 69 pedidos cancelados más los reintentos, lo que confirma la consistencia de la consulta con los datos.