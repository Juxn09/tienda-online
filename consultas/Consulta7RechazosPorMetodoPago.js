db.pedidos.aggregate([
  { $unwind: "$pagos" },
  { $group: {
      _id: "$pagos.metodo",
      intentos: { $sum: 1 },
      rechazados: { $sum: { $cond: [ { $eq: ["$pagos.estado", "Rechazado"] }, 1, 0 ] } },
      valorRechazado: { $sum: { $cond: [ { $eq: ["$pagos.estado", "Rechazado"] }, "$pagos.valor", 0 ] } },
      valorAprobado: { $sum: { $cond: [ { $eq: ["$pagos.estado", "Aprobado"] }, "$pagos.valor", 0 ] } }
  } },
  { $project: {
      _id: 0,
      metodo: "$_id",
      intentos: 1,
      rechazados: 1,
      tasaRechazo: { $round: [
        { $multiply: [ { $divide: ["$rechazados", "$intentos"] }, 100 ] },
        1
      ] },
      valorRechazado: 1,
      valorAprobado: 1
  } },
  { $sort: { tasaRechazo: -1 } }
])
