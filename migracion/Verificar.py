"""Verifica que la migración de SQL Server a MongoDB no perdió ni alteró información.

Capas de verificación:
  1. Conteos:      filas de cada tabla vs. documentos o elementos embebidos.
  2. Referencias:  todo id referenciado existe en su colección.
  3. Estructuras:  los arrays embebidos tienen los mismos elementos que en SQL.
  4. Contenido:    sumas de dinero y totales iguales.
  5. Puntuales:    pedidos de muestra comparados campo por campo.
"""
import os
from decimal import Decimal

from dotenv import load_dotenv
from pymongo import MongoClient

from Migrar import conectar_sql   # reutiliza la conexión (NO ejecuta la migración)

load_dotenv()

resultados = []   # True / False por cada verificación


# =================================================================
# Utilidades
# =================================================================
def revisar(descripcion, valor_sql, valor_mongo):
    """Compara dos valores, imprime OK o FALLA y guarda el resultado."""
    ok = valor_sql == valor_mongo
    resultados.append(ok)
    marca = "OK   " if ok else "FALLA"
    print(f"  [{marca}] {descripcion:<50} SQL={valor_sql}  MongoDB={valor_mongo}")


def escalar(cursor, consulta):
    """Ejecuta una consulta SQL que devuelve un solo valor."""
    cursor.execute(consulta)
    return cursor.fetchone()[0]


def agregar_uno(coleccion, pipeline, campo):
    """Ejecuta un pipeline que devuelve un solo documento y saca un campo (0 si no hay resultado)."""
    resultado = list(coleccion.aggregate(pipeline))
    return resultado[0][campo] if resultado else 0


def a_decimal(valor):
    """Decimal128 de MongoDB -> Decimal de Python, para comparar con SQL Server."""
    return valor.to_decimal() if hasattr(valor, "to_decimal") else Decimal(valor)


# =================================================================
# 1. CONTEOS
# =================================================================
def verificar_conteos(cursor, bd):
    print("\n1. CONTEOS")
    directas = [
        ("Categoria", "categorias"), ("Proveedor", "proveedores"), ("Producto", "productos"),
        ("Cliente", "clientes"), ("Pedido", "pedidos"), ("Resena", "resenas"),
    ]
    for tabla, coleccion in directas:
        revisar(f"{tabla} = documentos de {coleccion}",
                escalar(cursor, f"SELECT COUNT(*) FROM {tabla}"),
                bd[coleccion].count_documents({}))

    # Tablas que quedaron EMBEBIDAS: se cuentan los elementos de los arrays
    embebidas = [
        ("DetallePedido", "pedidos", "items"),
        ("Pago", "pedidos", "pagos"),
        ("Direccion", "clientes", "direcciones"),
    ]
    for tabla, coleccion, arreglo in embebidas:
        elementos = agregar_uno(bd[coleccion], [
            {"$group": {"_id": None, "n": {"$sum": {"$size": f"${arreglo}"}}}}
        ], "n")
        revisar(f"{tabla} = elementos de {coleccion}.{arreglo}",
                escalar(cursor, f"SELECT COUNT(*) FROM {tabla}"),
                elementos)

    revisar("Envio = pedidos con envio",
            escalar(cursor, "SELECT COUNT(*) FROM Envio"),
            bd.pedidos.count_documents({"envio": {"$ne": None}}))


# =================================================================
# 2. REFERENCIAS
# =================================================================
def referencias_rotas(coleccion, campo, destino, desenrollar=None):
    """Cuenta referencias que no encuentran su documento en la colección destino."""
    etapas = []
    if desenrollar:
        etapas.append({"$unwind": f"${desenrollar}"})     # un documento por elemento del array
    etapas += [
        {"$lookup": {"from": destino, "localField": campo,
                     "foreignField": "_id", "as": "encontrado"}},
        {"$match": {"encontrado": {"$size": 0}}},          # los que NO encontraron pareja
        {"$count": "rotas"},
    ]
    return agregar_uno(coleccion, etapas, "rotas")


def verificar_referencias(bd):
    print("\n2. REFERENCIAS (referencias rotas: deben ser 0)")
    casos = [
        ("pedidos.clienteId -> clientes",         bd.pedidos,   "clienteId",        "clientes",    None),
        ("pedidos.items.productoId -> productos", bd.pedidos,   "items.productoId", "productos",   "items"),
        ("productos.categoriaId -> categorias",   bd.productos, "categoriaId",      "categorias",  None),
        ("productos.proveedorId -> proveedores",  bd.productos, "proveedorId",      "proveedores", None),
        ("resenas.productoId -> productos",       bd.resenas,   "productoId",       "productos",   None),
        ("resenas.clienteId -> clientes",         bd.resenas,   "clienteId",        "clientes",    None),
    ]
    for descripcion, coleccion, campo, destino, desenrollar in casos:
        revisar(descripcion, 0, referencias_rotas(coleccion, campo, destino, desenrollar))


# =================================================================
# 3. ESTRUCTURAS EMBEBIDAS
# =================================================================
def conteo_por_pedido_sql(cursor, tabla):
    """{id_pedido: cantidad de filas} de una tabla hija."""
    cursor.execute(f"SELECT id_pedido, COUNT(*) FROM {tabla} GROUP BY id_pedido")
    return {fila[0]: fila[1] for fila in cursor.fetchall()}


def verificar_estructuras(cursor, bd):
    print("\n3. ESTRUCTURAS EMBEBIDAS")
    items_sql = conteo_por_pedido_sql(cursor, "DetallePedido")
    pagos_sql = conteo_por_pedido_sql(cursor, "Pago")

    distintos_items = 0
    distintos_pagos = 0
    for doc in bd.pedidos.find({}, {"items": 1, "pagos": 1}):
        if len(doc["items"]) != items_sql.get(doc["_id"], 0):
            distintos_items += 1
        if len(doc["pagos"]) != pagos_sql.get(doc["_id"], 0):
            distintos_pagos += 1
    revisar("Pedidos con distinta cantidad de items", 0, distintos_items)
    revisar("Pedidos con distinta cantidad de pagos", 0, distintos_pagos)

    despachados = ["Enviado", "Entregado"]
    incoherentes = (
        bd.pedidos.count_documents({"estado": {"$in": despachados}, "envio": None})
        + bd.pedidos.count_documents({"estado": {"$nin": despachados}, "envio": {"$ne": None}})
    )
    revisar("Pedidos con envio incoherente con su estado", 0, incoherentes)
    revisar("Pedidos sin items", 0, bd.pedidos.count_documents({"items": {"$size": 0}}))
    revisar("Totales que no son Decimal128", 0,
            bd.pedidos.count_documents({"total": {"$not": {"$type": "decimal"}}}))


# =================================================================
# 4. CONTENIDO
# =================================================================
def verificar_contenido(cursor, bd):
    print("\n4. CONTENIDO")
    ventas_mongo = agregar_uno(bd.pedidos, [
        {"$group": {"_id": None, "s": {"$sum": "$total"}}}
    ], "s")
    revisar("Suma de totales de pedidos",
            escalar(cursor, "SELECT SUM(total) FROM Pedido"),
            a_decimal(ventas_mongo))

    pagado_mongo = agregar_uno(bd.pedidos, [
        {"$unwind": "$pagos"},
        {"$match": {"pagos.estado": "Aprobado"}},
        {"$group": {"_id": None, "s": {"$sum": "$pagos.valor"}}},
    ], "s")
    revisar("Suma de pagos aprobados",
            escalar(cursor, "SELECT SUM(valor) FROM Pago WHERE estado = 'Aprobado'"),
            a_decimal(pagado_mongo))

    # El total de cada pedido debe ser la suma de sus items, calculada dentro de MongoDB
    descuadrados = agregar_uno(bd.pedidos, [
        {"$project": {
            "total": 1,
            "calculado": {"$sum": {"$map": {
                "input": "$items",
                "as": "i",
                "in": {"$subtract": [{"$multiply": ["$$i.cantidad", "$$i.precioUnitario"]},
                                     "$$i.descuento"]},
            }}},
        }},
        {"$match": {"$expr": {"$ne": ["$total", "$calculado"]}}},
        {"$count": "n"},
    ], "n")
    revisar("Pedidos cuyo total no es la suma de sus items", 0, descuadrados)


# =================================================================
# 5. DATOS PUNTUALES
# =================================================================
def verificar_puntuales(cursor, bd):
    print("\n5. DATOS PUNTUALES (pedidos de muestra, campo por campo)")
    muestra = list(range(1, 2001, 100)) + [150, 2000]
    diferencias = 0

    for id_pedido in muestra:
        # --- lo que dice SQL Server
        cursor.execute("SELECT id_cliente, id_direccion, fecha_pedido, estado, total "
                       "FROM Pedido WHERE id_pedido = ?", id_pedido)
        p = cursor.fetchone()
        cursor.execute("SELECT id_producto, cantidad, precio_unitario, descuento "
                       "FROM DetallePedido WHERE id_pedido = ? ORDER BY id_producto", id_pedido)
        items_sql = [tuple(fila) for fila in cursor.fetchall()]
        cursor.execute("SELECT numero_guia FROM Envio WHERE id_pedido = ?", id_pedido)
        fila_envio = cursor.fetchone()
        guia_sql = fila_envio[0] if fila_envio else None

        # --- lo que dice MongoDB
        doc = bd.pedidos.find_one({"_id": id_pedido})
        items_mongo = sorted(
            (i["productoId"], i["cantidad"], a_decimal(i["precioUnitario"]), a_decimal(i["descuento"]))
            for i in doc["items"]
        )
        guia_mongo = doc["envio"]["numeroGuia"] if doc["envio"] else None

        iguales = (
            doc["clienteId"] == p.id_cliente
            and doc["direccionEnvio"]["idDireccion"] == p.id_direccion
            and doc["fechaPedido"] == p.fecha_pedido
            and doc["estado"] == p.estado
            and a_decimal(doc["total"]) == p.total
            and items_mongo == items_sql
            and guia_mongo == guia_sql
        )
        if not iguales:
            diferencias += 1
            print(f"     Diferencia en el pedido {id_pedido}")

    revisar(f"Pedidos con diferencias ({len(muestra)} revisados)", 0, diferencias)


# =================================================================
# Programa principal
# =================================================================
def main():
    conexion = conectar_sql()
    cursor = conexion.cursor()
    cliente = MongoClient(os.getenv("MONGO_URI"))
    bd = cliente[os.getenv("MONGO_DATABASE")]

    print("VERIFICACIÓN DE LA MIGRACIÓN  SQL Server -> MongoDB")
    verificar_conteos(cursor, bd)
    verificar_referencias(bd)
    verificar_estructuras(cursor, bd)
    verificar_contenido(cursor, bd)
    verificar_puntuales(cursor, bd)

    conexion.close()
    cliente.close()

    fallas = resultados.count(False)
    print(f"\nResultado: {len(resultados) - fallas} de {len(resultados)} verificaciones correctas.")
    if fallas == 0:
        print("MIGRACIÓN VERIFICADA: no se perdió ni se alteró información.")
    else:
        print("HAY DIFERENCIAS: revisar las líneas marcadas con FALLA.")


if __name__ == "__main__":
    main()