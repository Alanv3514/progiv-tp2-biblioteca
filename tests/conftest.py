import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlalchemy.pool import StaticPool

# registra TODAS las tablas en SQLModel.metadata
import models.autor  # noqa: F401
import models.libro  # noqa: F401
import models.libro_autor  # noqa: F401
import models.prestamo  # noqa: F401
import models.socio  # noqa: F401

import main
from database import get_session


@pytest.fixture
def engine():
    # SQLite en memoria con StaticPool: la misma conexion para Tests y app
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    yield engine
    engine.dispose()


@pytest.fixture
def client(engine):
    def override_get_session():
        with Session(engine) as session:
            yield session

    main.app.dependency_overrides[get_session] = override_get_session
    with TestClient(main.app) as test_client:
        yield test_client
    main.app.dependency_overrides.clear()


@pytest.fixture
def session(engine):
    return Session(engine)


@pytest.fixture
def socio_id(client) -> int:
    response = client.post(
        "/socios", json={"nombre": "Juan Perez", "email": "juan@example.com"}
    )
    return response.json()["id"]


@pytest.fixture
def libro_id(client) -> int:
    response = client.post(
        "/libros",
        json={
            "titulo": "Python en accion",
            "isbn": "111",
            "stock": 3,
            "anio": 2024,
        },
    )
    return response.json()["id"]
