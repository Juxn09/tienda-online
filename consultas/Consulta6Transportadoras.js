db.pedidos.aggregate([
  { $match: { "envio.estado": "Entregado" } },
  { $project: {
      transportadora: "$envio.transportadora",
      horasDespacho: { $dateDiff: {
        startDate: "$fechaPedido",
        endDate: "$envio.fechaEnvio",
        unit: "hour"
      } },
      horasEntrega: { $dateDiff: {
        startDate: "$envio.fechaEnvio",
        endDate: "$envio.fechaEntrega",
        unit: "hour"
      } }
  } },
  { $group: {
      _id: "$transportadora",
      envios: { $sum: 1 },
      promedioEntrega: { $avg: "$horasEntrega" },
      maximoEntrega: { $max: "$horasEntrega" },
      tardios: { $sum: { $cond: [ { $gt: ["$horasEntrega", 96] }, 1, 0 ] } },
      promedioDespacho: { $avg: "$horasDespacho" }
  } },
  { $project: {
      _id: 0,
      transportadora: "$_id",
      envios: 1,
      diasEntregaPromedio: { $round: [ { $divide: ["$promedioEntrega", 24] }, 2 ] },
      diasEntregaMaximo: { $round: [ { $divide: ["$maximoEntrega", 24] }, 1 ] },
      porcentajeTardios: { $round: [
        { $multiply: [ { $divide: ["$tardios", "$envios"] }, 100 ] },
        1
      ] },
      diasDespachoTienda: { $round: [ { $divide: ["$promedioDespacho", 24] }, 2 ] }
  } },
  { $sort: { diasEntregaPromedio: 1 } }
])
