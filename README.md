# Tienda en línea: migración SQL Server → MongoDB

Taller Evaluativo No. 3 – Bases de Datos II  
Profesor: Juan Carlos Gómez  
Integrantes: Juan Camilo Moreno, Marshall Robinson

## Descripción

Base de datos relacional de una tienda en línea en SQL Server (10 entidades, 14.595 registros), migrada con Python a un modelo documental en MongoDB que aplica **Embedding** (detalles, pagos, envío y direcciones dentro de sus documentos) y **Referencing** (clientes, productos, categorías y proveedores como colecciones independientes). La migración se comprueba con 25 verificaciones automáticas y se analiza con 7 consultas de negocio usando Aggregation Pipeline.

## Resultados principales

| | |
|---|---|
| Modelo relacional | 10 tablas · 14.595 registros · 11 reglas de coherencia con 0 violaciones |
| Modelo documental | 6 colecciones · 4.325 documentos |
| Verificación | 25 de 25 comprobaciones correctas + prueba negativa |
| Consultas | 7 pipelines con `$match`, `$project`, `$group`, `$sort`, `$limit`, `$unwind` y `$lookup` múltiples |

## Estructura del repositorio

| Ruta | Contenido |
|---|---|
| `sql/CrearTablas.sql` | Crea la base `TiendaOnline` con 10 tablas, restricciones e índices |
| `sql/CargarDatos.sql` | Genera 14.595 registros coherentes y reproducibles |
| `sql/VerificarCoherencia.sql` | 11 reglas de negocio verificadas sobre los datos de SQL Server |
| `migracion/ProbarConexion.py` | Prueba las conexiones a SQL Server y MongoDB |
| `migracion/Migrar.py` | Migración ETL: extrae, transforma (embebe/referencia) y carga en MongoDB |
| `migracion/Verificar.py` | Compara SQL Server y MongoDB en 5 capas |
| `consultas/` | Las 7 consultas de agregación, comentadas |
| `docs/modelo_relacional.md` | Modelo relacional, relaciones y decisiones de diseño |
| `docs/ModeloDocumental.md` | Modelo documental y justificación de Embedding vs. Referencing |
| `docs/Verificacion.md` | Cómo se comprobó que no se perdió información |
| `docs/Consultas.md` | Necesidad, decisión, impacto e interpretación de cada consulta |
| `evidencias/` | Capturas y salida de la verificación |
| `presentacion/` | Presentación para la sustentación |

## Tecnologías

- SQL Server 2025 Express + SQL Server Management Studio
- Python 3.14 con `pyodbc`, `pymongo` y `python-dotenv`
- ODBC Driver 18 for SQL Server
- MongoDB 8.3 + MongoDB Compass (mongosh integrado)

## Cómo ejecutar

### 1. Requisitos

SQL Server con SSMS, MongoDB en `localhost:27017`, Python 3.12 o superior y el ODBC Driver 18 for SQL Server.

### Descargar el proyecto

```powershell
git clone https://github.com/Juxn09/tienda-online.git
cd tienda-online
```

### 2. Crear y cargar la base relacional

En SSMS, abrir y ejecutar completos (F5), en este orden:

1. `sql/CrearTablas.sql`
2. `sql/CargarDatos.sql`
3. `sql/VerificarCoherencia.sql` (opcional: todas las reglas deben dar 0)

### 3. Preparar Python

Desde la carpeta del proyecto:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

### 4. Configurar la conexión

Copiar `.env.example` como `.env` y cambiar `SQL_SERVER` por el nombre del servidor propio (por ejemplo `MIEQUIPO\SQLEXPRESS`). El archivo `.env` no se sube al repositorio.

```powershell
python migracion\ProbarConexion.py
```

### 5. Migrar y verificar

```powershell
python migracion\Migrar.py
python migracion\Verificar.py
```

La verificación debe terminar con `25 de 25 verificaciones correctas`. La migración se puede repetir: borra y recarga las colecciones.

### 6. Ejecutar las consultas

En MongoDB Compass, abrir la terminal mongosh, ejecutar `use TiendaOnline` y pegar el contenido de cualquier archivo de `consultas/`.