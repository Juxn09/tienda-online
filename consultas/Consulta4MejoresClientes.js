db.pedidos.aggregate([
  { $match: { estado: { $in: ["Pagado", "Enviado", "Entregado"] } } },
  { $group: {
      _id: "$clienteId",
      pedidos: { $sum: 1 },
      totalComprado: { $sum: "$total" },
      ultimaCompra: { $max: "$fechaPedido" }
  } },
  { $sort: { totalComprado: -1 } },
  { $limit: 10 },
  { $lookup: {
      from: "clientes",
      localField: "_id",
      foreignField: "_id",
      as: "cliente"
  } },
  { $unwind: "$cliente" },
  { $addFields: {
      principal: { $first: { $filter: {
        input: "$cliente.direcciones",
        as: "d",
        cond: { $eq: ["$$d.esPrincipal", true] }
      } } }
  } },
  { $project: {
      _id: 0,
      clienteId: "$_id",
      nombre: { $concat: ["$cliente.nombres", " ", "$cliente.apellidos"] },
      ciudad: "$principal.ciudad",
      pedidos: 1,
      totalComprado: 1,
      ticketPromedio: { $round: [ { $divide: ["$totalComprado", "$pedidos"] }, 0 ] },
      ultimaCompra: 1
  } }
])
