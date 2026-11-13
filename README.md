# Stockmaster

API REST para gestionar el inventario y las ventas de Stockmaster. El proyecto usa Django y Django REST Framework; permite administrar personas, tipos de persona, categorías, artículos, ventas y detalles de factura.

## Requisitos

- Python 3.12 o superior
- `pip`
- SQL Server con el controlador ODBC 18 para SQL Server
- Instalar Ollama (llama3.2:3b)


## Instalación local

Desde la raíz del repositorio, crea y activa un entorno virtual:

```powershell
py -m venv .venv
\.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
$env:DJANGO_SETTINGS_MODULE = "config.settings"
```

La aplicación usa SQL Server exclusivamente. Configura las variables de conexión de la sección SQL Server antes de inicializar la base de datos y ejecutar el servidor:

```powershell
python -m django makemigrations stockmaster
python -m django migrate
python -m django runserver
```

Las rutas de la API quedan disponibles bajo `http://127.0.0.1:8000/api/`.

## Recursos de la API

Todas las rutas siguientes requieren autenticación, excepto la obtención y renovación del token.

| Recurso | Ruta | Métodos |
|---|---|---|
| Índice de la API | `/api/` | GET |
| Tipos de persona | `/api/tipo-persona/` | GET, POST |
| Tipo de persona individual | `/api/tipo-persona/{id}/` | GET, PUT, PATCH, DELETE |
| Personas | `/api/persona/` | GET, POST |
| Persona individual | `/api/persona/{id}/` | GET, PUT, PATCH, DELETE |
| Ventas | `/api/venta/` | GET, POST |
| Venta individual | `/api/venta/{id}/` | GET, PUT, PATCH, DELETE |
| Detalles de factura | `/api/detalle-factura/` | GET, POST |
| Detalle individual | `/api/detalle-factura/{id}/` | GET, PUT, PATCH, DELETE |
| Artículos | `/api/articulo/` | GET, POST |
| Artículo individual | `/api/articulo/{codigo}/` | GET, PUT, PATCH, DELETE |
| Categorías | `/api/categoria/` | GET, POST |
| Categoría individual | `/api/categoria/{id}/` | GET, PUT, PATCH, DELETE |
| Conversaciones de IA | `/api/ia/conversaciones/` | GET, POST |
| Conversación individual | `/api/ia/conversaciones/{id}/` | GET, PUT, PATCH, DELETE |
| Mensajes de una conversación | `/api/ia/conversaciones/{id}/mensajes/` | GET, POST |
| Obtener token JWT | `/api/token/` | POST |
| Renovar token JWT | `/api/token/refresh/` | POST |

Las rutas de detalle de los recursos de Stockmaster aceptan `PUT`, `PATCH` y `DELETE`. Usa la barra final en todas las rutas.

## Crear el administrador y agregar usuarios

Después de configurar SQL Server y aplicar las migraciones, crea el usuario administrador de Django (superusuario):

```powershell
python manage.py migrate
python manage.py createsuperuser
```

Sigue las indicaciones de la consola para definir nombre de usuario, correo y contraseña. Inicia el servidor y entra al panel administrativo:

```powershell
python manage.py runserver
```

Abre `http://127.0.0.1:8000/admin/` e inicia sesión con las credenciales del superusuario. En **Users**, selecciona **Add user** para crear otras cuentas de Django. Un usuario normal puede autenticarse en la API, pero solo los usuarios con permisos de staff pueden entrar al panel administrativo.

Usa el `username` y la contraseña de cada cuenta de Django para obtener su JWT en `/api/token/`. Si el usuario también utilizará las conversaciones de IA, crea además su registro `Persona` y asegúrate de que `Persona.usuario` sea idéntico al `username` de Django; esta asociación no se crea automáticamente.

## Autenticación JWT

El token se obtiene con un usuario de Django, creado por ejemplo con `python -m django createsuperuser`. En Postman:

1. Selecciona el método `POST` y la URL `http://127.0.0.1:8000/api/token/`.
2. En **Body → raw → JSON**, envía las credenciales del usuario de Django:

```json
{
	"username": "ana",
	"password": "tu_contraseña"
}
```

La respuesta contiene los campos `access` y `refresh`. Para llamar a una ruta protegida, en Postman selecciona **Authorization → Bearer Token** y pega el valor de `access`. También puedes enviar la cabecera `Authorization: Bearer <access>`.

Cuando expire el token de acceso, solicita otro con `POST http://127.0.0.1:8000/api/token/refresh/` y este JSON:

```json
{
	"refresh": "<refresh>"
}
```

La respuesta incluye un nuevo `access`. La interfaz navegable de Django REST Framework también permite iniciar sesión en `http://127.0.0.1:8000/api-auth/login/`.

### Usuario de Django y Persona

La autenticación JWT utiliza el usuario de Django (`auth.User`), pero las conversaciones de IA se relacionan con el modelo `Persona`. Por eso, el campo `Persona.usuario` debe coincidir exactamente con el `username` del usuario de Django. Por ejemplo, si el token se obtiene con `username: "ana"`, debe existir una persona con `usuario: "ana"`.

Si no coinciden, el usuario podrá autenticarse, pero no podrá crear conversaciones de IA; además, el listado de conversaciones estará vacío. La contraseña enviada a `/api/token/` es la contraseña del usuario de Django.

## SQL Server

Para usar SQL Server, instala el controlador ODBC 18 y configura estas variables de entorno antes de iniciar Django:

| Variable | Ejemplo |
|---|---|
| `DATABASE_ENGINE` | `mssql` |
| `DATABASE_NAME` | `StockMaster_BD` |
| `DATABASE_USER` | usuario de la base de datos |
| `DATABASE_PASSWORD` | contraseña local |
| `DATABASE_HOST` | `127.0.0.1` |
| `DATABASE_PORT` | `1433` |
| `DATABASE_DRIVER` | `ODBC Driver 18 for SQL Server` |

No guardes contraseñas ni claves en el repositorio. Para despliegues, define también `DJANGO_SECRET_KEY`, `DJANGO_DEBUG=false` y `DJANGO_ALLOWED_HOSTS` con los hosts autorizados.

## Pruebas

```powershell
python -m django makemigrations
python -m django migrate
python -m django runserver
```

Asegúrate de que el servidor SQL acepte conexiones TCP/IP y que el puerto `1433` esté habilitado. No guardes contraseñas ni claves en el repositorio. Para despliegues, define también `DJANGO_SECRET_KEY`, `DJANGO_DEBUG=false` y `DJANGO_ALLOWED_HOSTS` con los hosts autorizados.

## Pruebas

El estado actual del proyecto tiene 6 pruebas fallidas de 11: las pruebas de ventas esperan cálculo automático de subtotales/totales y creación de detalles anidados que todavía no están implementados.

## Estructura

```text
config/       Configuración y rutas del proyecto Django
stockmaster/  Modelos, serializadores, vistas y pruebas de la aplicación
```
