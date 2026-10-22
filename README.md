# Tienda en línea: migración SQL Server → MongoDB

Taller Evaluativo No. 3 – Bases de Datos II  
Profesor: Juan Carlos Gómez  
Integrantes: Juan Camilo , Marshall Robinson 

## Descripción
Base de datos relacional de una tienda en línea (10 entidades, ~15.000 registros)
en SQL Server, migrada con Python a un modelo documental en MongoDB que aplica
Embedding y Referencing. Incluye verificación de la migración y consultas con
Aggregation Pipeline.

## Estructura
| Carpeta | Contenido |
|---|---|
| `sql/` | Scripts de creación y carga de la base relacional |
| `migracion/` | Script de migración y de verificación en Python |
| `consultas/` | Consultas de MongoDB (Aggregation Pipeline) |
| `docs/` | Modelo relacional, modelo documental y justificaciones |
| `evidencias/` | Capturas de estructura, datos y verificaciones |
| `presentacion/` | Presentación para la sustentación |

## Tecnologías
- SQL Server 2025 Express + SSMS
- Python 3.14 (pyodbc, pymongo, python-dotenv)
- MongoDB 8.3 + MongoDB Compass

## Cómo ejecutar
(se completará al final del proyecto)