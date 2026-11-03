# TP2 — Sistema de Biblioteca (FastAPI + SQLModel)

API REST para gestionar el catálogo de una biblioteca y sus préstamos,
con **FastAPI** + **SQLModel** (SQLite), reglas de negocio en una capa
`services` y tests con cobertura de código.

- Documentación interactiva (Swagger): **`http://127.0.0.1:8000/docs`**

## Modelo de datos

| Entidad      | Campos                                                                    |
| ------------ | ------------------------------------------------------------------------- |
| `Autor`      | id, nombre, nacionalidad                                                  |
| `Libro`      | id, titulo, isbn (único), stock (≥ 0), anio                               |
| `LibroAutor` | libro_id, autor_id (tabla intermedia, N-N)                                |
| `Socio`      | id, nombre, email (único), activo                                         |
| `Prestamo`   | id, socio_id, libro_id, fecha_prestamo, fecha_vencimiento, fecha_devolucion, multa |

## Estructura

```
models/     entidades SQLModel y esquemas de entrada/salida
routers/    endpoints por entidad
services/   reglas de negocio de préstamos
tests/      pytest sobre una base en memoria
```

## Cómo correr

```bash
python -m venv .venv

# Windows (PowerShell)
.venv\Scripts\Activate.ps1

# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
uvicorn main:app --reload
```

Abrí `http://127.0.0.1:8000/docs` para probar todos los endpoints desde
Swagger UI.

## Cómo testear

Con el entorno virtual activado (requiere `requirements-dev.txt`):

```bash
pip install -r requirements-dev.txt
pytest
```

`pytest.ini` configura cobertura mínima (`--cov-fail-under=80`); la
corrida actual reporta **96%**. Los tests corren sobre una base SQLite
en memoria (`conftest.py`), así que no dejan archivos ni estado.

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
