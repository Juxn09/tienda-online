/* =========================================================
   Consulta 2: Ventas por categoría y su porcentaje del total
   Necesidad: saber qué categorías generan más ingresos para
              repartir el presupuesto de marketing.
   Etapas: $match, $unwind, $group x2, $lookup x2,
           $setWindowFields, $project, $sort
   ========================================================= */
db.pedidos.aggregate([
  // 1. Solo ventas efectivas
  { $match: { estado: { $in: ["Pagado", "Enviado", "Entregado"] } } },

  // 2. Un documento por item
  { $unwind: "$items" },

  // 3. Primer agrupamiento: por PRODUCTO (5.000 items -> 300 productos)
  { $group: {
      _id: "$items.productoId",
      unidades: { $sum: "$items.cantidad" },
      ingresos: { $sum: { $subtract: [
        { $multiply: ["$items.cantidad", "$items.precioUnitario"] },
        "$items.descuento"
      ] } }
  } },

  // 4. Traer el producto para conocer su categoría
  { $lookup: {
      from: "productos",
      localField: "_id",
      foreignField: "_id",
      as: "producto"
  } },
  { $unwind: "$producto" },

  // 5. Segundo agrupamiento: por CATEGORÍA (300 productos -> 10 categorías)
  { $group: {
      _id: "$producto.categoriaId",
      ingresos: { $sum: "$ingresos" },
      unidades: { $sum: "$unidades" },
      productosVendidos: { $sum: 1 }
  } },

  // 6. Traer el nombre de la categoría
  { $lookup: {
      from: "categorias",
      localField: "_id",
      foreignField: "_id",
      as: "categoria"
  } },
  { $unwind: "$categoria" },

  // 7. Agregar a cada categoría el total general de ingresos
  { $setWindowFields: {
      output: {
        totalGeneral: { $sum: "$ingresos" }
      }
  } },

  // 8. Calcular el porcentaje y dejar los campos útiles
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

  // 9. La categoría que más vende primero
  { $sort: { ingresos: -1 } }
])