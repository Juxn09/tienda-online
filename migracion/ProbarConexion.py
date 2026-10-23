"""Prueba las conexiones a SQL Server y MongoDB usando los datos del archivo .env."""
import os

import pyodbc
from dotenv import load_dotenv
from pymongo import MongoClient

# Lee el archivo .env y deja sus valores disponibles con os.getenv()
load_dotenv()

# Cadena de conexión a SQL Server
cadena_sql = (
    f"DRIVER={{{os.getenv('SQL_DRIVER')}}};"
    f"SERVER={os.getenv('SQL_SERVER')};"
    f"DATABASE={os.getenv('SQL_DATABASE')};"
    "Trusted_Connection=yes;"        # autenticación de Windows
    "TrustServerCertificate=yes;"    # servidor local sin certificado
)

conexion = pyodbc.connect(cadena_sql)
cursor = conexion.cursor()
cursor.execute("SELECT COUNT(*) FROM Pedido")
print("SQL Server OK - pedidos:", cursor.fetchone()[0])
conexion.close()

# Conexión a MongoDB (espera máximo 3 segundos)
cliente = MongoClient(os.getenv("MONGO_URI"), serverSelectionTimeoutMS=3000)
print("MongoDB OK - versión:", cliente.server_info()["version"])
cliente.close()