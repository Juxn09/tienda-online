db.resenas.aggregate([
  { $lookup: {
      from: "productos",
      localField: "productoId",
      foreignField: "_id",
      as: "producto"
  } },
  { $unwind: "$producto" },
  { $group: {
      _id: "$producto.proveedorId",
      promedio: { $avg: "$calificacion" },
      resenas: { $sum: 1 },
      negativas: { $sum: { $cond: [ { $lte: ["$calificacion", 2] }, 1, 0 ] } }
  } },
  { $match: { resenas: { $gte: 20 } } },
  { $lookup: {
      from: "proveedores",
      localField: "_id",
      foreignField: "_id",
      as: "proveedor"
  } },
  { $unwind: "$proveedor" },
  { $project: {
      _id: 0,
      proveedor: "$proveedor.razonSocial",
      ciudad: "$proveedor.ciudad",
      resenas: 1,
      calificacionPromedio: { $round: ["$promedio", 2] },
      porcentajeNegativas: { $round: [
        { $multiply: [ { $divide: ["$negativas", "$resenas"] }, 100 ] },
        1
      ] }
  } },
  { $sort: { calificacionPromedio: 1, porcentajeNegativas: -1 } },
  { $limit: 5 }
])
