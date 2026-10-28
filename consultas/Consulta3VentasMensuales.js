db.pedidos.aggregate([
  { $match: { estado: { $in: ["Pagado", "Enviado", "Entregado"] } } },
  { $group: {
      _id: { $dateToString: { format: "%Y-%m", date: "$fechaPedido" } },
      pedidos: { $sum: 1 },
      ventas: { $sum: "$total" },
      ticketPromedio: { $avg: "$total" }
  } },
  { $sort: { _id: 1 } },
  { $project: {
      _id: 0,
      mes: "$_id",
      pedidos: 1,
      ventas: 1,
      ticketPromedio: { $round: ["$ticketPromedio", 0] }
  } }
])
