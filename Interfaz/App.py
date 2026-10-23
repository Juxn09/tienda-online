"""Interfaz web de la base TiendaOnline (MongoDB) para la sustentación."""
import contextlib
import io
import os
import sys

import pandas as pd
import streamlit as st
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()
st.set_page_config(page_title="Tienda en línea", page_icon="🛒", layout="wide")

# ---------------------------------------------------------------- estilo
st.markdown("""
<style>
.block-container {padding-top: 2rem;}
.tarjeta {background: #EAF3F1; border-radius: 12px; padding: 18px 20px; height: 100%;}
.tarjeta .numero {font-size: 2rem; font-weight: 700; color: #0F766E; line-height: 1.1;}
.tarjeta .etiqueta {font-size: 0.95rem; color: #475569;}
.chip {display: inline-block; padding: 2px 10px; border-radius: 999px; font-size: 0.8rem;
       font-weight: 600; color: white; margin-left: 6px;}
.embebido {background: #0F766E;} .referencia {background: #0369A1;} .copia {background: #D97706;}
</style>
""", unsafe_allow_html=True)


def tarjeta(columna, numero, etiqueta):
    columna.markdown(f'<div class="tarjeta"><div class="numero">{numero}</div>'
                     f'<div class="etiqueta">{etiqueta}</div></div>', unsafe_allow_html=True)


def chip(texto, clase):
    return f'<span class="chip {clase}">{texto}</span>'


def pesos(valor):
    """Formato de dinero colombiano: $1.234.567"""
    return "$" + f"{float(valor):,.0f}".replace(",", ".")


def a_numero(valor):
    """Decimal128 de MongoDB -> float de Python (para tablas y gráficos)."""
    return float(valor.to_decimal()) if hasattr(valor, "to_decimal") else valor


def tabla(documentos):
    filas = [{k: a_numero(v) for k, v in doc.items()} for doc in documentos]
    return pd.DataFrame(filas)


DINERO = {"ingresos", "ventas", "ticketPromedio", "totalComprado", "valorRechazado",
          "precioUnitario", "descuento", "valor"}


def mostrar(df, primera=None):
    """Tabla con la columna principal primero y el dinero con separador de miles."""
    if primera in df.columns:
        df = df[[primera] + [c for c in df.columns if c != primera]]
    formato = {c: st.column_config.NumberColumn(f"{c} ($)", format="localized")
               for c in df.columns if c in DINERO}
    st.dataframe(df, hide_index=True, use_container_width=True, column_config=formato)


# ---------------------------------------------------------------- conexión
@st.cache_resource
def conectar():
    cliente = MongoClient(os.getenv("MONGO_URI"), serverSelectionTimeoutMS=3000)
    return cliente[os.getenv("MONGO_DATABASE")]


bd = conectar()

# ---------------------------------------------------------------- consultas
VENTAS = {"$match": {"estado": {"$in": ["Pagado", "Enviado", "Entregado"]}}}
SUBTOTAL = {"$subtract": [{"$multiply": ["$items.cantidad", "$items.precioUnitario"]}, "$items.descuento"]}


def unir(coleccion, local, como):
    """$lookup + $unwind: sigue una referencia y convierte el array en objeto."""
    return [{"$lookup": {"from": coleccion, "localField": local, "foreignField": "_id", "as": como}},
            {"$unwind": f"${como}"}]


CONSULTAS = {
    "1 · Productos más vendidos": {
        "pregunta": "¿Cuáles son los 10 productos más vendidos y de qué categoría son?",
        "decision": "Priorizar la reposición de inventario de los productos que más rotan.",
        "coleccion": "pedidos",
        "pipeline": [VENTAS, {"$unwind": "$items"},
                     {"$group": {"_id": "$items.productoId", "unidades": {"$sum": "$items.cantidad"},
                                 "pedidos": {"$sum": 1}, "ingresos": {"$sum": SUBTOTAL}}},
                     {"$sort": {"unidades": -1, "ingresos": -1}}, {"$limit": 10},
                     *unir("productos", "_id", "producto"), *unir("categorias", "producto.categoriaId", "categoria"),
                     {"$project": {"_id": 0, "producto": "$producto.nombre", "categoria": "$categoria.nombre",
                                   "unidades": 1, "pedidos": 1, "ingresos": 1, "stock": "$producto.stock"}}],
        "grafico": ("producto", "unidades"),
    },
    "2 · Ventas por categoría": {
        "pregunta": "¿Cuánto vende cada categoría y qué porcentaje del total representa?",
        "decision": "Repartir el presupuesto de marketing según el peso de cada categoría.",
        "coleccion": "pedidos",
        "pipeline": [VENTAS, {"$unwind": "$items"},
                     {"$group": {"_id": "$items.productoId", "unidades": {"$sum": "$items.cantidad"},
                                 "ingresos": {"$sum": SUBTOTAL}}},
                     *unir("productos", "_id", "producto"),
                     {"$group": {"_id": "$producto.categoriaId", "ingresos": {"$sum": "$ingresos"},
                                 "unidades": {"$sum": "$unidades"}}},
                     *unir("categorias", "_id", "categoria"),
                     {"$setWindowFields": {"output": {"total": {"$sum": "$ingresos"}}}},
                     {"$project": {"_id": 0, "categoria": "$categoria.nombre", "ingresos": 1, "unidades": 1,
                                   "porcentaje": {"$round": [{"$multiply": [{"$divide": [
                                       {"$toDouble": "$ingresos"}, {"$toDouble": "$total"}]}, 100]}, 2]}}},
                     {"$sort": {"ingresos": -1}}],
        "grafico": ("categoria", "porcentaje"),
    },
    "3 · Ventas mes a mes": {
        "pregunta": "¿Cómo evolucionan las ventas mes a mes?",
        "decision": "Planear inventario, personal y campañas según los meses fuertes y débiles.",
        "coleccion": "pedidos",
        "pipeline": [VENTAS,
                     {"$group": {"_id": {"$dateToString": {"format": "%Y-%m", "date": "$fechaPedido"}},
                                 "pedidos": {"$sum": 1}, "ventas": {"$sum": "$total"},
                                 "ticketPromedio": {"$avg": "$total"}}},
                     {"$sort": {"_id": 1}},
                     {"$project": {"_id": 0, "mes": "$_id", "pedidos": 1, "ventas": 1,
                                   "ticketPromedio": {"$round": ["$ticketPromedio", 0]}}}],
        "grafico": ("mes", "ventas"),
        "linea": True,
    },
    "4 · Mejores clientes": {
        "pregunta": "¿Quiénes son los 10 mejores clientes y de qué ciudad son?",
        "decision": "Programa de fidelización diferenciado (clientes frecuentes vs. de alto ticket).",
        "coleccion": "pedidos",
        "pipeline": [VENTAS,
                     {"$group": {"_id": "$clienteId", "pedidos": {"$sum": 1}, "totalComprado": {"$sum": "$total"},
                                 "ultimaCompra": {"$max": "$fechaPedido"}}},
                     {"$sort": {"totalComprado": -1}}, {"$limit": 10},
                     *unir("clientes", "_id", "cliente"),
                     {"$addFields": {"principal": {"$first": {"$filter": {
                         "input": "$cliente.direcciones", "as": "d", "cond": {"$eq": ["$$d.esPrincipal", True]}}}}}},
                     {"$project": {"_id": 0, "cliente": {"$concat": ["$cliente.nombres", " ", "$cliente.apellidos"]},
                                   "ciudad": "$principal.ciudad", "pedidos": 1, "totalComprado": 1,
                                   "ultimaCompra": 1}}],
        "grafico": ("cliente", "totalComprado"),
    },
    "5 · Proveedores peor calificados": {
        "pregunta": "¿Qué proveedores tienen la peor calificación?",
        "decision": "Renegociar calidad o reemplazar a los proveedores con más reseñas negativas.",
        "coleccion": "resenas",
        "pipeline": [*unir("productos", "productoId", "producto"),
                     {"$group": {"_id": "$producto.proveedorId", "promedio": {"$avg": "$calificacion"},
                                 "resenas": {"$sum": 1},
                                 "negativas": {"$sum": {"$cond": [{"$lte": ["$calificacion", 2]}, 1, 0]}}}},
                     {"$match": {"resenas": {"$gte": 20}}},
                     *unir("proveedores", "_id", "proveedor"),
                     {"$project": {"_id": 0, "proveedor": "$proveedor.razonSocial", "ciudad": "$proveedor.ciudad",
                                   "resenas": 1, "calificacion": {"$round": ["$promedio", 2]},
                                   "negativasPct": {"$round": [{"$multiply": [
                                       {"$divide": ["$negativas", "$resenas"]}, 100]}, 1]}}},
                     {"$sort": {"calificacion": 1, "negativasPct": -1}}, {"$limit": 5}],
        "grafico": ("proveedor", "calificacion"),
    },
    "6 · Transportadoras": {
        "pregunta": "¿Qué transportadora entrega más rápido?",
        "decision": "Elegir transportadora y fijar un acuerdo de nivel de servicio (SLA).",
        "coleccion": "pedidos",
        "pipeline": [{"$match": {"envio.estado": "Entregado"}},
                     {"$project": {"transportadora": "$envio.transportadora",
                                   "horasDespacho": {"$dateDiff": {"startDate": "$fechaPedido",
                                                                   "endDate": "$envio.fechaEnvio", "unit": "hour"}},
                                   "horasEntrega": {"$dateDiff": {"startDate": "$envio.fechaEnvio",
                                                                  "endDate": "$envio.fechaEntrega", "unit": "hour"}}}},
                     {"$group": {"_id": "$transportadora", "envios": {"$sum": 1},
                                 "entrega": {"$avg": "$horasEntrega"}, "despacho": {"$avg": "$horasDespacho"},
                                 "tardios": {"$sum": {"$cond": [{"$gt": ["$horasEntrega", 96]}, 1, 0]}}}},
                     {"$project": {"_id": 0, "transportadora": "$_id", "envios": 1,
                                   "diasEntrega": {"$round": [{"$divide": ["$entrega", 24]}, 2]},
                                   "tardiosPct": {"$round": [{"$multiply": [
                                       {"$divide": ["$tardios", "$envios"]}, 100]}, 1]},
                                   "diasDespachoTienda": {"$round": [{"$divide": ["$despacho", 24]}, 2]}}},
                     {"$sort": {"diasEntrega": 1}}],
        "grafico": ("transportadora", "diasEntrega"),
    },
    "7 · Rechazos por método de pago": {
        "pregunta": "¿Qué método de pago tiene más rechazos?",
        "decision": "Revisar la pasarela de pagos y el orden de los métodos en el pago.",
        "coleccion": "pedidos",
        "pipeline": [{"$unwind": "$pagos"},
                     {"$group": {"_id": "$pagos.metodo", "intentos": {"$sum": 1},
                                 "rechazados": {"$sum": {"$cond": [{"$eq": ["$pagos.estado", "Rechazado"]}, 1, 0]}},
                                 "valorRechazado": {"$sum": {"$cond": [{"$eq": ["$pagos.estado", "Rechazado"]},
                                                                       "$pagos.valor", 0]}}}},
                     {"$project": {"_id": 0, "metodo": "$_id", "intentos": 1, "rechazados": 1,
                                   "tasaRechazo": {"$round": [{"$multiply": [
                                       {"$divide": ["$rechazados", "$intentos"]}, 100]}, 1]},
                                   "valorRechazado": 1}},
                     {"$sort": {"tasaRechazo": -1}}],
        "grafico": ("metodo", "tasaRechazo"),
    },
}

# ---------------------------------------------------------------- menú
with st.sidebar:
    st.markdown("## 🛒 Tienda en línea")
    st.caption("SQL Server → MongoDB · Taller 3 BD2")
    pagina = st.radio("Sección", ["Resumen", "Consultas", "Buscar pedido", "Verificación"],
                      label_visibility="collapsed")
    st.divider()
    st.caption("Juan Camilo Moreno · Marshall Robinson")

# ================================================================ RESUMEN
if pagina == "Resumen":
    st.title("Migración de SQL Server a MongoDB")
    st.write("Base de datos **TiendaOnline**: 10 tablas relacionales convertidas en 6 colecciones "
             "aplicando Embedding y Referencing.")

    conteos = {c: bd[c].count_documents({}) for c in
               ["categorias", "proveedores", "productos", "clientes", "pedidos", "resenas"]}
    columnas = st.columns(6)
    for col, (nombre, n) in zip(columnas, conteos.items()):
        tarjeta(col, f"{n:,}".replace(",", "."), nombre)

    st.write("")
    ventas = list(bd.pedidos.aggregate([VENTAS, {"$group": {"_id": None, "s": {"$sum": "$total"}}}]))[0]["s"]
    embebidos = list(bd.pedidos.aggregate([{"$group": {"_id": None,
                                                       "items": {"$sum": {"$size": "$items"}},
                                                       "pagos": {"$sum": {"$size": "$pagos"}}}}]))[0]
    c1, c2, c3 = st.columns(3)
    tarjeta(c1, pesos(a_numero(ventas)), "ventas efectivas")
    tarjeta(c2, f"{embebidos['items']:,}".replace(",", "."), "items embebidos en pedidos")
    tarjeta(c3, f"{embebidos['pagos']:,}".replace(",", "."), "pagos embebidos en pedidos")

    st.subheader("De 10 tablas a 6 colecciones")
    st.markdown(f"""
| Tablas SQL Server | Colección | Técnica |
|---|---|---|
| Pedido + DetallePedido + Pago + Envio | `pedidos` | {chip("Embebido", "embebido")} items, pagos, envío · {chip("Referencia", "referencia")} cliente, producto |
| Cliente + Direccion | `clientes` | {chip("Embebido", "embebido")} direcciones |
| Producto | `productos` | {chip("Referencia", "referencia")} categoría y proveedor |
| Resena | `resenas` | {chip("Referencia", "referencia")} producto y cliente |
| Categoria · Proveedor | `categorias` · `proveedores` | Catálogos referenciados |
""", unsafe_allow_html=True)

# ================================================================ CONSULTAS
elif pagina == "Consultas":
    st.title("Consultas de negocio")
    nombre = st.selectbox("Consulta", list(CONSULTAS.keys()))
    c = CONSULTAS[nombre]

    izq, der = st.columns(2)
    izq.info(f"**Pregunta:** {c['pregunta']}")
    der.success(f"**Decisión que apoya:** {c['decision']}")

    df = tabla(bd[c["coleccion"]].aggregate(c["pipeline"]))
    x, y = c["grafico"]
    if c.get("linea"):
        st.line_chart(df, x=x, y=y, color="#0F766E")
    else:
        st.bar_chart(df, x=x, y=y, color="#0F766E", horizontal=True, sort=False)
    mostrar(df, x)

    with st.expander("Ver el pipeline de agregación"):
        st.json(c["pipeline"], expanded=False)

# ================================================================ BUSCAR PEDIDO
elif pagina == "Buscar pedido":
    st.title("Buscar un pedido")
    st.write("Un solo documento de MongoDB reúne lo que en SQL Server estaba en **5 tablas**.")
    id_pedido = st.number_input("Número de pedido", min_value=1, max_value=2000, value=150, step=1)
    pedido = bd.pedidos.find_one({"_id": int(id_pedido)})

    if pedido is None:
        st.warning("No existe ese pedido.")
    else:
        cliente = bd.clientes.find_one({"_id": pedido["clienteId"]})   # seguir la referencia
        c1, c2, c3, c4 = st.columns(4)
        tarjeta(c1, pedido["estado"], "estado")
        tarjeta(c2, pesos(a_numero(pedido["total"])), "total")
        tarjeta(c3, pedido["fechaPedido"].strftime("%d/%m/%Y"), "fecha del pedido")
        tarjeta(c4, len(pedido["items"]), "productos")

        st.write("")
        izq, der = st.columns(2)
        with izq:
            st.markdown(f"#### Cliente {chip('Referencia', 'referencia')}", unsafe_allow_html=True)
            st.write(f"**clienteId: {pedido['clienteId']}** → {cliente['nombres']} {cliente['apellidos']}  \n"
                     f"{cliente['email']}")
        with der:
            d = pedido["direccionEnvio"]
            st.markdown(f"#### Dirección de envío {chip('Copia histórica', 'copia')}", unsafe_allow_html=True)
            st.write(f"**{d['alias']}** · {d['direccion']}  \n{d['ciudad']}, {d['departamento']}")

        st.markdown(f"#### Items {chip('Embebido', 'embebido')}", unsafe_allow_html=True)
        mostrar(tabla(pedido["items"]), "nombre")

        izq, der = st.columns(2)
        with izq:
            st.markdown(f"#### Pagos {chip('Embebido', 'embebido')}", unsafe_allow_html=True)
            mostrar(tabla(pedido["pagos"]), "metodo")
        with der:
            st.markdown(f"#### Envío {chip('Embebido', 'embebido')}", unsafe_allow_html=True)
            if pedido["envio"] is None:
                st.write("Este pedido todavía no se ha despachado (`envio: null`).")
            else:
                e = pedido["envio"]
                st.write(f"**{e['transportadora']}** · guía {e['numeroGuia']}  \n"
                         f"Enviado: {e['fechaEnvio']:%d/%m/%Y %H:%M}  \n"
                         f"Entregado: {e['fechaEntrega']:%d/%m/%Y %H:%M}" if e["fechaEntrega"] else
                         f"**{e['transportadora']}** · guía {e['numeroGuia']}  \nEn tránsito")

        with st.expander("Ver el documento completo (JSON)"):
            st.json({k: str(v) if not isinstance(v, (list, dict, int, str)) else v
                     for k, v in pedido.items()}, expanded=False)

# ================================================================ VERIFICACIÓN
else:
    st.title("Verificación de la migración")
    st.write("Compara SQL Server contra MongoDB en 5 capas: conteos, referencias, estructuras, "
             "contenido y datos puntuales.")

    if st.button("▶ Ejecutar verificación", type="primary"):
        carpeta = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "migracion")
        sys.path.insert(0, carpeta)
        import Verificar   # reutiliza el script de la fase 5

        Verificar.resultados.clear()
        salida = io.StringIO()
        with st.spinner("Comparando SQL Server y MongoDB..."), contextlib.redirect_stdout(salida):
            Verificar.main()
        correctas = Verificar.resultados.count(True)
        total = len(Verificar.resultados)

        if correctas == total:
            st.success(f"✅ {correctas} de {total} verificaciones correctas: no se perdió información.")
        else:
            st.error(f"❌ {correctas} de {total} verificaciones correctas: hay diferencias.")
        st.code(salida.getvalue(), language=None)