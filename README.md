# Stockmaster

API REST para gestionar el inventario y las ventas de Stockmaster. El proyecto usa Django y Django REST Framework; permite administrar personas, tipos de persona, categorías, artículos, ventas y detalles de factura.

## Requisitos

- Python 3.12 o superior
- `pip`
- SQLite (incluido con Python) para desarrollo, o SQL Server con el controlador ODBC 18 para SQL Server

## Instalación local

Desde la raíz del repositorio, crea y activa un entorno virtual:

```powershell
py -m venv .venv
\.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
$env:DJANGO_SETTINGS_MODULE = "config.settings"
```

La configuración predeterminada usa SQLite y no requiere credenciales. Inicializa la base de datos y ejecuta el servidor:

```powershell
python -m django makemigrations stockmaster
python -m django migrate
python -m django runserver
```

Las rutas de la API quedan disponibles bajo `http://127.0.0.1:8000/api/`.

## Recursos de la API

| Recurso | Ruta |
|---|---|
| Tipos de persona | `/api/tipo-persona/` |
| Personas | `/api/persona/` |
| Ventas | `/api/venta/` |
| Detalles de factura | `/api/detalle-factura/` |
| Artículos | `/api/articulo/` |
| Categorías | `/api/categoria/` |

Cada ruta es un `ModelViewSet` de Django REST Framework y ofrece las operaciones CRUD estándar. Por ejemplo:

```http
GET http://127.0.0.1:8000/api/articulo/
```

## SQL Server

Para usar SQL Server con Django, instala SQL Server Developer o SQL Server Express y el controlador ODBC 18 para SQL Server. Luego crea la base de datos y configura estas variables de entorno antes de iniciar Django:

```powershell
$env:DATABASE_ENGINE = "mssql"
$env:DATABASE_NAME = "StockMaster_BD"
$env:DATABASE_USER = "sa"
$env:DATABASE_PASSWORD = "TuPasswordSegura"
$env:DATABASE_HOST = "127.0.0.1"
$env:DATABASE_PORT = "1433"
$env:DATABASE_DRIVER = "ODBC Driver 18 for SQL Server"
$env:DATABASE_EXTRA_PARAMS = "TrustServerCertificate=yes;"
$env:DJANGO_SETTINGS_MODULE = "config.settings"
```

Si aún no existe la base de datos, créala en SQL Server:

```sql
CREATE DATABASE StockMaster_BD;
GO
```

Luego, para generar y aplicar las migraciones sobre SQL Server:

```powershell
python -m django makemigrations stockmaster
python -m django migrate
python -m django runserver
```

Asegúrate de que el servidor SQL acepte conexiones TCP/IP y que el puerto `1433` esté habilitado. No guardes contraseñas ni claves en el repositorio. Para despliegues, define también `DJANGO_SECRET_KEY`, `DJANGO_DEBUG=false` y `DJANGO_ALLOWED_HOSTS` con los hosts autorizados.

## Pruebas

```powershell
python -m django test stockmaster
```

El estado actual del proyecto tiene 6 pruebas fallidas de 11: las pruebas de ventas esperan cálculo automático de subtotales/totales y creación de detalles anidados que todavía no están implementados correctamente.

## Estructura

```text
config/       Configuración y rutas del proyecto Django
stockmaster/  Modelos, serializadores, vistas y pruebas de la aplicación
```
