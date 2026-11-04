import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

# registra TODAS las tablas en SQLModel.metadata
import models.autor  # noqa: F401
import models.libro  # noqa: F401
import models.libro_autor  # noqa: F401
import models.prestamo  # noqa: F401
import models.socio  # noqa: F401

import main
import database


EMAIL_BIBLIOTECARIO = "biblio@biblioteca.com"
PASSWORD_DE_PRUEBA = "1234"


@pytest.fixture(name="engine")
def engine_fixture():
    # SQLite en memoria con StaticPool: la misma conexion para Tests y app
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,                      # ver nota abajo
    )
    SQLModel.metadata.create_all(engine)
    yield engine
    engine.dispose()


@pytest.fixture(name="client")
def client_fixture(engine, monkeypatch):
    # apunta el engine de la app al de memoria, asi los tests no tocan
    # el database.db de produccion y usan el get_session real
    monkeypatch.setattr(database, "engine", engine)
    with TestClient(main.app) as test_client:
        yield test_client


@pytest.fixture(name="session")
def session_fixture(engine):
    return Session(engine)


@pytest.fixture(name="login")
def login_fixture(client):
    def _login(email: str, password: str = PASSWORD_DE_PRUEBA) -> dict:
        res = client.post("/login", json={"email": email, "password": password})
        assert res.status_code == 200, res.text
        return {"Authorization": f"Bearer {res.json()['token']}"}

    return _login


@pytest.fixture(name="biblio_headers")
def biblio_headers_fixture(client, login):
    return login(EMAIL_BIBLIOTECARIO)


@pytest.fixture(name="socio_id")
def socio_id_fixture(client):
    response = client.post(
        "/socios",
        json={
            "nombre": "Juan Perez",
            "email": "juan@example.com",
            "password": PASSWORD_DE_PRUEBA,
        },
    )
    return response.json()["id"]


@pytest.fixture(name="libro_id")
def libro_id_fixture(client, biblio_headers):
    response = client.post(
        "/libros",
        json={
            "titulo": "Python en accion",
            "isbn": "111",
            "stock": 3,
            "anio": 2024,
        },
        headers=biblio_headers,
    )
    return response.json()["id"]
