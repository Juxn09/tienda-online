db.pedidos.aggregate([
  { $match: { estado: { $in: ["Pagado", "Enviado", "Entregado"] } } },
  { $unwind: "$items" },
  { $group: {
      _id: "$items.productoId",
      unidades: { $sum: "$items.cantidad" },
      pedidos: { $sum: 1 },
      ingresos: { $sum: { $subtract: [
        { $multiply: ["$items.cantidad", "$items.precioUnitario"] },
        "$items.descuento"
      ] } }
  } },
  { $sort: { unidades: -1, ingresos: -1 } },
  { $limit: 10 },
  { $lookup: {
      from: "productos",
      localField: "_id",
      foreignField: "_id",
      as: "producto"
  } },
  { $unwind: "$producto" },
  { $lookup: {
      from: "categorias",
      localField: "producto.categoriaId",
      foreignField: "_id",
      as: "categoria"
  } },
  { $unwind: "$categoria" },
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
