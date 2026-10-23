"""Migra la base TiendaOnline de SQL Server a MongoDB aplicando Embedding y Referencing.

Etapas (ETL):
  1. Extraer:     leer las 10 tablas de SQL Server.
  2. Transformar: armar los documentos de las 6 colecciones.
  3. Cargar:      insertar los documentos en MongoDB.
"""
import os
from collections import defaultdict
from datetime import datetime

import pyodbc
from bson.decimal128 import Decimal128
from dotenv import load_dotenv
from pymongo import ASCENDING, MongoClient

load_dotenv()


# =================================================================
# Utilidades
# =================================================================
def conectar_sql():
    """Abre la conexión a SQL Server con los datos del .env."""
    cadena = (
        f"DRIVER={{{os.getenv('SQL_DRIVER')}}};"
        f"SERVER={os.getenv('SQL_SERVER')};"
        f"DATABASE={os.getenv('SQL_DATABASE')};"
        "Trusted_Connection=yes;"
        "TrustServerCertificate=yes;"
    )
    return pyodbc.connect(cadena)


def leer_tabla(cursor, consulta):
    """Ejecuta una consulta y devuelve una lista de diccionarios {columna: valor}."""
    cursor.execute(consulta)
    columnas = [col[0] for col in cursor.description]
    return [dict(zip(columnas, fila)) for fila in cursor.fetchall()]


def agrupar(filas, campo):
    """Agrupa filas por un campo: {valor_del_campo: [fila, fila, ...]}."""
    grupos = defaultdict(list)
    for fila in filas:
        grupos[fila[campo]].append(fila)
    return grupos


def dinero(valor):
    """DECIMAL de SQL Server (Decimal en Python) -> Decimal128 de MongoDB (exacto)."""
    return Decimal128(valor)


def fecha(valor):
    """DATE de SQL Server -> datetime a medianoche (MongoDB no tiene tipo solo-fecha)."""
    return datetime(valor.year, valor.month, valor.day)


# =================================================================
# 1. EXTRAER
# =================================================================
def extraer(cursor):
    print("1. Extrayendo datos de SQL Server...")
    datos = {
        "Categoria":     leer_tabla(cursor, "SELECT * FROM Categoria ORDER BY id_categoria"),
        "Proveedor":     leer_tabla(cursor, "SELECT * FROM Proveedor ORDER BY id_proveedor"),
        "Producto":      leer_tabla(cursor, "SELECT * FROM Producto ORDER BY id_producto"),
        "Cliente":       leer_tabla(cursor, "SELECT * FROM Cliente ORDER BY id_cliente"),
        "Direccion":     leer_tabla(cursor, "SELECT * FROM Direccion ORDER BY id_direccion"),
        "Pedido":        leer_tabla(cursor, "SELECT * FROM Pedido ORDER BY id_pedido"),
        "DetallePedido": leer_tabla(cursor, "SELECT * FROM DetallePedido ORDER BY id_pedido, id_producto"),
        "Pago":          leer_tabla(cursor, "SELECT * FROM Pago ORDER BY id_pago"),
        "Envio":         leer_tabla(cursor, "SELECT * FROM Envio ORDER BY id_envio"),
        "Resena":        leer_tabla(cursor, "SELECT * FROM Resena ORDER BY id_resena"),
    }
    for tabla, filas in datos.items():
        print(f"   {tabla:<14} {len(filas):>6} filas")
    return datos


# =================================================================
# 2. TRANSFORMAR
# =================================================================
def transformar_categorias(categorias):
    return [
        {
            "_id": c["id_categoria"],
            "nombre": c["nombre"],
            "descripcion": c["descripcion"],
        }
        for c in categorias
    ]


def transformar_proveedores(proveedores):
    return [
        {
            "_id": p["id_proveedor"],
            "nit": p["nit"],
            "razonSocial": p["razon_social"],
            "ciudad": p["ciudad"],
            "telefono": p["telefono"],
            "email": p["email"],
        }
        for p in proveedores
    ]


def transformar_productos(productos):
    return [
        {
            "_id": p["id_producto"],
            "sku": p["sku"],
            "nombre": p["nombre"],
            "descripcion": p["descripcion"],
            "precio": dinero(p["precio"]),
            "stock": p["stock"],
            "activo": p["activo"],
            "categoriaId": p["id_categoria"],    # REFERENCIA -> categorias
            "proveedorId": p["id_proveedor"],    # REFERENCIA -> proveedores
        }
        for p in productos
    ]


def transformar_clientes(clientes, direcciones):
    """Cliente + Direccion -> un documento con las direcciones EMBEBIDAS."""
    direcciones_por_cliente = agrupar(direcciones, "id_cliente")

    documentos = []
    for c in clientes:
        documentos.append({
            "_id": c["id_cliente"],
            "documento": c["documento"],
            "nombres": c["nombres"],
            "apellidos": c["apellidos"],
            "email": c["email"],
            "telefono": c["telefono"],
            "fechaRegistro": fecha(c["fecha_registro"]),
            "direcciones": [                                   # EMBEBIDO
                {
                    "idDireccion": d["id_direccion"],
                    "alias": d["alias"],
                    "direccion": d["direccion"],
                    "ciudad": d["ciudad"],
                    "departamento": d["departamento"],
                    "esPrincipal": d["es_principal"],
                }
                for d in direcciones_por_cliente[c["id_cliente"]]
            ],
        })
    return documentos


def transformar_pedidos(pedidos, detalles, pagos, envios, direcciones, productos):
    """Pedido + DetallePedido + Pago + Envio (+ copia de Direccion) -> un documento."""
    detalles_por_pedido = agrupar(detalles, "id_pedido")
    pagos_por_pedido = agrupar(pagos, "id_pedido")
    envio_por_pedido = {e["id_pedido"]: e for e in envios}          # 1 : 0..1
    direccion_por_id = {d["id_direccion"]: d for d in direcciones}
    nombre_producto = {p["id_producto"]: p["nombre"] for p in productos}

    documentos = []
    for p in pedidos:
        dir_envio = direccion_por_id[p["id_direccion"]]
        envio = envio_por_pedido.get(p["id_pedido"])                # None si no tiene

        documentos.append({
            "_id": p["id_pedido"],
            "clienteId": p["id_cliente"],                            # REFERENCIA -> clientes
            "fechaPedido": p["fecha_pedido"],
            "estado": p["estado"],
            "total": dinero(p["total"]),
            "direccionEnvio": {                                      # COPIA histórica
                "idDireccion": dir_envio["id_direccion"],
                "alias": dir_envio["alias"],
                "direccion": dir_envio["direccion"],
                "ciudad": dir_envio["ciudad"],
                "departamento": dir_envio["departamento"],
            },
            "items": [                                               # EMBEBIDO (DetallePedido)
                {
                    "productoId": det["id_producto"],                # REFERENCIA -> productos
                    "nombre": nombre_producto[det["id_producto"]],   # referencia extendida
                    "cantidad": det["cantidad"],
                    "precioUnitario": dinero(det["precio_unitario"]),
                    "descuento": dinero(det["descuento"]),
                }
                for det in detalles_por_pedido[p["id_pedido"]]
            ],
            "pagos": [                                               # EMBEBIDO (Pago)
                {
                    "idPago": pg["id_pago"],
                    "fechaPago": pg["fecha_pago"],
                    "metodo": pg["metodo"],
                    "valor": dinero(pg["valor"]),
                    "estado": pg["estado"],
                }
                for pg in pagos_por_pedido[p["id_pedido"]]
            ],
            "envio": None if envio is None else {                    # EMBEBIDO (Envio) o null
                "idEnvio": envio["id_envio"],
                "transportadora": envio["transportadora"],
                "numeroGuia": envio["numero_guia"],
                "fechaEnvio": envio["fecha_envio"],
                "fechaEntrega": envio["fecha_entrega"],
                "estado": envio["estado"],
            },
        })
    return documentos


def transformar_resenas(resenas):
    return [
        {
            "_id": r["id_resena"],
            "productoId": r["id_producto"],      # REFERENCIA -> productos
            "clienteId": r["id_cliente"],        # REFERENCIA -> clientes
            "calificacion": r["calificacion"],
            "comentario": r["comentario"],
            "fecha": fecha(r["fecha"]),
        }
        for r in resenas
    ]


# =================================================================
# 3. CARGAR
# =================================================================
def cargar(bd, colecciones):
    print("3. Cargando en MongoDB...")
    for nombre, documentos in colecciones.items():
        bd[nombre].drop()                     # borra la colección si existe (migración repetible)
        bd[nombre].insert_many(documentos)
        print(f"   {nombre:<12} {bd[nombre].count_documents({}):>6} documentos")


def crear_indices(bd):
    """Índices sobre los campos de referencia (aceleran los $lookup de las consultas)."""
    bd.productos.create_index([("categoriaId", ASCENDING)])
    bd.productos.create_index([("proveedorId", ASCENDING)])
    bd.pedidos.create_index([("clienteId", ASCENDING)])
    bd.pedidos.create_index([("items.productoId", ASCENDING)])
    bd.resenas.create_index([("productoId", ASCENDING)])
    bd.resenas.create_index([("clienteId", ASCENDING)])
    print("   Índices creados.")


# =================================================================
# Programa principal
# =================================================================
def main():
    conexion = conectar_sql()
    datos = extraer(conexion.cursor())
    conexion.close()

    print("2. Transformando a documentos...")
    colecciones = {
        "categorias":  transformar_categorias(datos["Categoria"]),
        "proveedores": transformar_proveedores(datos["Proveedor"]),
        "productos":   transformar_productos(datos["Producto"]),
        "clientes":    transformar_clientes(datos["Cliente"], datos["Direccion"]),
        "pedidos":     transformar_pedidos(datos["Pedido"], datos["DetallePedido"], datos["Pago"],
                                           datos["Envio"], datos["Direccion"], datos["Producto"]),
        "resenas":     transformar_resenas(datos["Resena"]),
    }

    cliente = MongoClient(os.getenv("MONGO_URI"))
    bd = cliente[os.getenv("MONGO_DATABASE")]
    cargar(bd, colecciones)
    crear_indices(bd)
    cliente.close()
    print("Migración terminada.")


if __name__ == "__main__":
    main()