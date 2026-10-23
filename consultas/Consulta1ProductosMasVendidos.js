/* =========================================================
   Consulta 1: Top 10 productos más vendidos y su categoría
   Necesidad: saber qué productos rotan más para priorizar
              su reposición de inventario.
   Etapas: $match, $unwind, $group, $sort, $limit,
           $lookup x2 (productos -> categorias), $project
   ========================================================= */
db.pedidos.aggregate([
  // 1. Solo ventas efectivas: sin pedidos Pendientes ni Cancelados
  { $match: { estado: { $in: ["Pagado", "Enviado", "Entregado"] } } },

  // 2. Un documento por cada producto comprado (desarma el array items)
  { $unwind: "$items" },

  // 3. Agrupar por producto: unidades, en cuántos pedidos aparece e ingresos
  { $group: {
      _id: "$items.productoId",
      unidades: { $sum: "$items.cantidad" },
      pedidos: { $sum: 1 },
      ingresos: { $sum: { $subtract: [
        { $multiply: ["$items.cantidad", "$items.precioUnitario"] },
        "$items.descuento"
      ] } }
  } },

  // 4. Más unidades primero; si empatan, más ingresos
  { $sort: { unidades: -1, ingresos: -1 } },

  // 5. Solo el top 10 (antes de los $lookup: se unen 10 documentos, no 300)
  { $limit: 10 },

  // 6. Traer el producto (referencia) y convertir el array en objeto
  { $lookup: {
      from: "productos",
      localField: "_id",
      foreignField: "_id",
      as: "producto"
  } },
  { $unwind: "$producto" },

  // 7. Traer la categoría usando el categoriaId que trajo el producto
  { $lookup: {
      from: "categorias",
      localField: "producto.categoriaId",
      foreignField: "_id",
      as: "categoria"
  } },
  { $unwind: "$categoria" },

  // 8. Mostrar solo lo útil, con nombres claros
  { $project: {
      _id: 0,
      productoId: "$_id",
      producto: "$producto.nombre",
      categoria: "$categoria.nombre",
      unidades: 1,
      pedidos: 1,
      ingresos: 1,
      stockActual: "$producto.stock"
  } }
])