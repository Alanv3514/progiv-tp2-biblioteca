# TP2 — Sistema de Biblioteca (FastAPI + SQLModel)

API REST para gestionar el catálogo de una biblioteca y sus préstamos,
con **FastAPI** + **SQLModel** (SQLite), reglas de negocio en una capa
`services` y tests con cobertura de código.

- Documentación interactiva (Swagger): **`http://127.0.0.1:8000/docs`**

## Requisitos

- Python 3.12 o más nuevo
- pip

## Cómo correr

```bash
# 1. crear entorno virtual
python3 -m venv .venv

# 2. activarlo
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# 3. instalar dependencias
pip install -r requirements.txt

# 4. levantar la API
uvicorn main:app --reload
```

- Swagger con todos los endpoints: `http://127.0.0.1:8000/docs`
- En el primer arranque la app crea `database.db` y siembra un
  bibliotecario (ver Roles abajo).

## Roles (parte opcional del TP)

| Rol | Puede |
|---|---|
| `bibliotecario` | administra el catálogo (autores, libros), socios, préstamos y devoluciones |
| `socio` | se auto-registra via `POST /socios`, pide préstamos propios y ve únicamente sus préstamos |

Los endpoints quedan así:

| Acceso | Endpoints |
|---|---|
| Público | `POST /login`, `POST /socios` (auto-registro), consultas del catálogo (`GET`) |
| Socio autenticado | `POST /prestamos` (solo para su propio socio), `GET /socios/{id}/prestamos` (solo los suyos) |
| Solo bibliotecario | alta/baja/modificación de autores, libros y socios, `DELETE`, asociar autor a libro, `POST /prestamos/{id}/devolucion` |

### Cómo loguearse

```bash
curl -X POST http://127.0.0.1:8000/login \
  -H "Content-Type: application/json" \
  -d '{"email": "biblio@biblioteca.com", "password": "1234"}'
```

Devuelve `{"msg": "ok", "token": "..."}`. Para llamar endpoints
protegidos, mandá el header:

```
Authorization: Bearer <token>
```

En Swagger: botón **Authorize**, pegar `Bearer <token>`.

- Bibliotecario sembrado en el primer arranque: `biblio@biblioteca.com` / `1234`
- Los socios se registran por `POST /socios` con `nombre`, `email` y
  `password` (mínimo 4 caracteres). El password se guarda hasheado con
  bcrypt.
- El token JWT expira a los 30 minutos.

## Modelo de datos

| Entidad      | Campos                                                                    |
| ------------ | ------------------------------------------------------------------------- |
| `Autor`      | id, nombre, nacionalidad                                                  |
| `Libro`      | id, titulo, isbn (único), stock (≥ 0), anio                               |
| `LibroAutor` | libro_id, autor_id (tabla intermedia, N-N)                                |
| `Socio`      | id, nombre, email (único), password (hasheado), activo, rol               |
| `Prestamo`   | id, socio_id, libro_id, fecha_prestamo, fecha_vencimiento, fecha_devolucion, multa |

## Estructura

Según lo que sugiere la consigna del TP:

```
models/     entidades SQLModel y esquemas de entrada/salida
routers/    endpoints por entidad (+ /login)
services/   reglas de negocio de préstamos, JWT
utils/      helpers (hash de contraseñas con bcrypt)
tests/      pytest sobre una base en memoria
```

Otros archivos: `dependencies.py` (dependencias de sesión, JWT y roles,
como en la clase de SQLModel), `database.py` (engine y `get_session`),
`main.py` (app, router y seed del bibliotecario en el startup).

## Cómo testear

Con el entorno virtual activado:

```bash
pytest
```

`pytest.ini` configura cobertura mínima (`--cov-fail-under=80`); la
corrida actual reporta **100%**. Los tests corren sobre una base SQLite
en memoria (`tests/conftest.py`), así que no dejan archivos ni estado.

## Lint y chequeo de tipos

Igual que en la clase de FastAPI, el proyecto incluye configuración
local para dos herramientas:

- **`setup.cfg`**: configuración de `pycodestyle` (chequeo de estilo
  PEP 8). Define `max-line-length = 130` y excluye `.venv` y
  `__pycache__` del análisis.
- **`pyrightconfig.json`**: configuración de `pyright` (chequeo de
  tipos). Apunta al entorno virtual local (`.venv`). `pyright` ya viene
  en `requirements.txt`; `pycodestyle` se instala aparte.

```bash
pip install pycodestyle
python -m pycodestyle .
pyright
```

## Reglas de negocio implementadas

| # | Regla | Error |
|---|-------|-------|
| 1 | Un socio no puede tener más de 3 préstamos activos | `409` |
| 2 | No se presta sin stock; al prestar se descuenta 1 | `409` |
| 3 | Un socio inactivo no puede pedir préstamos | `403` |
| 4 | Vencimiento = fecha de préstamo + 14 días | n/a |
| 5 | Al devolver se repone stock y multa = 100 × días de atraso (0 a tiempo) | n/a |
| 6 | No se puede devolver un préstamo ya devuelto | `409` |
| 7 | Recurso inexistente | `404` |
| 8 | ISBN o email duplicado | `409` |
| + | Token ausente o inválido | `401` |
| + | Rol insuficiente (ej. socio queriendo administrar el catálogo) | `403` |
| + | Un socio solo registra préstamos propios y ve sus propios préstamos | `403` |
