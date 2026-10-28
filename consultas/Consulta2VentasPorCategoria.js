db.pedidos.aggregate([
  { $match: { estado: { $in: ["Pagado", "Enviado", "Entregado"] } } },
  { $unwind: "$items" },
  { $group: {
      _id: "$items.productoId",
      unidades: { $sum: "$items.cantidad" },
      ingresos: { $sum: { $subtract: [
        { $multiply: ["$items.cantidad", "$items.precioUnitario"] },
        "$items.descuento"
      ] } }
  } },
  { $lookup: {
      from: "productos",
      localField: "_id",
      foreignField: "_id",
      as: "producto"
  } },
  { $unwind: "$producto" },
  { $group: {
      _id: "$producto.categoriaId",
      ingresos: { $sum: "$ingresos" },
      unidades: { $sum: "$unidades" },
      productosVendidos: { $sum: 1 }
  } },
  { $lookup: {
      from: "categorias",
      localField: "_id",
      foreignField: "_id",
      as: "categoria"
  } },
  { $unwind: "$categoria" },
  { $setWindowFields: {
      output: {
        totalGeneral: { $sum: "$ingresos" }
      }
  } },
  { $project: {
      _id: 0,
      categoria: "$categoria.nombre",
      ingresos: 1,
      unidades: 1,
      productosVendidos: 1,
      porcentaje: { $round: [
        { $multiply: [
          { $divide: [ { $toDouble: "$ingresos" }, { $toDouble: "$totalGeneral" } ] },
          100
        ] },
        2
      ] }
  } },
  { $sort: { ingresos: -1 } }
])
