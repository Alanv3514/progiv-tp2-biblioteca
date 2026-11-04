"""Tests de reglas de negocio de prestamos (reglas 1 a 6) y roles."""

from datetime import datetime, timedelta


def crear_socio(client, email: str):
    return client.post(
        "/socios", json={"nombre": "Nombre", "email": email, "password": "1234"}
    )


def prestar(client, socio_id: int, libro_id: int, headers):
    return client.post(
        "/prestamos", json={"socio_id": socio_id, "libro_id": libro_id}, headers=headers
    )


def test_login_fallido(client):
    r = client.post("/login", json={"email": "nadie@x.com", "password": "123"})
    assert r.status_code == 401
    crear_socio(client, "clave@x.com")
    r = client.post("/login", json={"email": "clave@x.com", "password": "mala"})
    assert r.status_code == 401


def test_token_invalido(client):
    r = client.get("/socios/1/prestamos", headers={"Authorization": "Bearer no-es-jwt"})
    assert r.status_code == 401


def test_socio_eliminado_invalidate_token(client, biblio_headers, login):
    socio = crear_socio(client, "borrado@x.com").json()
    headers = login("borrado@x.com")
    client.delete(f"/socios/{socio['id']}", headers=biblio_headers)
    r = client.get(f"/socios/{socio['id']}/prestamos", headers=headers)
    assert r.status_code == 401


def test_prestamo_de_socio_ajeno_bloqueado_para_socio(client, biblio_headers, login):
    otro = crear_socio(client, "ajeno@x.com").json()
    libro_id = client.post(
        "/libros",
        json={"titulo": "T", "isbn": "pj", "stock": 2, "anio": 2024},
        headers=biblio_headers,
    ).json()["id"]
    socio = crear_socio(client, "pide@x.com").json()
    r = prestar(client, otro["id"], libro_id, login("pide@x.com"))
    assert r.status_code == 403

    # el bibliotecario si puede prestar para otro socio
    r = prestar(client, otro["id"], libro_id, biblio_headers)
    assert r.status_code == 201


def test_prestamo_feliz(client, socio_id, libro_id, login):
    r = prestar(client, socio_id, libro_id, login("juan@example.com"))
    assert r.status_code == 201
    prestamo = r.json()
    prestado = datetime.fromisoformat(prestamo["fecha_prestamo"])
    venc = datetime.fromisoformat(prestamo["fecha_vencimiento"])
    assert venc - prestado == timedelta(days=14)
    assert prestamo["fecha_devolucion"] is None
    assert prestamo["multa"] == 0
    assert client.get(f"/libros/{libro_id}").json()["stock"] == 2  # 3 - 1


def test_socio_inexistente_y_libro_inexistente(client, biblio_headers, login):
    socio = crear_socio(client, "cual@x.com").json()
    headers = login("cual@x.com")
    r = prestar(client, 999, 1, headers)
    assert r.status_code == 404
    # socio valido, libro inexistente
    r = prestar(client, socio["id"], 999, headers)
    assert r.status_code == 404


def test_socio_inactivo_no_puede_prestar(client, biblio_headers, libro_id, login):
    socio = crear_socio(client, "i@x.com").json()
    client.put(
        f"/socios/{socio['id']}", json={"activo": False}, headers=biblio_headers
    )
    r = prestar(client, socio["id"], libro_id, login("i@x.com"))
    assert r.status_code == 403


def test_max_tres_prestamos_activos(client, biblio_headers, login):
    libro_id = client.post(
        "/libros",
        json={"titulo": "T", "isbn": "max", "stock": 9, "anio": 2024},
        headers=biblio_headers,
    ).json()["id"]
    crear_socio(client, "v@x.com")
    headers = login("v@x.com")
    for _ in range(3):
        assert prestar(client, _socio_de(client, "v@x.com"), libro_id, headers).status_code == 201
    r = prestar(client, _socio_de(client, "v@x.com"), libro_id, headers)
    assert r.status_code == 409


def _socio_de(client, email: str) -> int:
    socios = client.get("/socios").json()
    return next(s["id"] for s in socios if s["email"] == email)


def test_libro_sin_stock(client, biblio_headers, socio_id, login):
    libro = client.post(
        "/libros",
        json={"titulo": "NoStock", "isbn": "ns", "stock": 0, "anio": 2024},
        headers=biblio_headers,
    ).json()
    r = prestar(client, socio_id, libro["id"], login("juan@example.com"))
    assert r.status_code == 409


def test_prestamo_descuenta_stock(client, socio_id, libro_id, login):
    prestar(client, socio_id, libro_id, login("juan@example.com"))
    r = client.get(f"/libros/{libro_id}")
    assert r.json()["stock"] == 2  # 3 - 1


def test_devolucion_a_tiempo(client, socio_id, libro_id, biblio_headers, login):
    prestamo = prestar(client, socio_id, libro_id, login("juan@example.com")).json()
    stock_antes = client.get(f"/libros/{libro_id}").json()["stock"]
    r = client.post(
        f"/prestamos/{prestamo['id']}/devolucion", headers=biblio_headers
    )
    assert r.status_code == 200
    devuelto = r.json()
    assert devuelto["multa"] == 0
    assert devuelto["fecha_devolucion"] is not None
    # repone stock
    assert client.get(f"/libros/{libro_id}").json()["stock"] == stock_antes + 1


def test_devolucion_con_atraso_aplica_multa(
    client, socio_id, libro_id, biblio_headers, login, session
):
    prestamo = prestar(client, socio_id, libro_id, login("juan@example.com")).json()

    # simula un prestamo hecho hace 20 dias (14 de plazo -> 6 dias de atraso)
    from sqlmodel import select
    from models.prestamo import Prestamo

    prestamo_db = session.exec(
        select(Prestamo).where(Prestamo.id == prestamo["id"])
    ).one()
    prestamo_db.fecha_prestamo = datetime.now() - timedelta(days=20)
    prestamo_db.fecha_vencimiento = prestamo_db.fecha_prestamo + timedelta(days=14)
    session.add(prestamo_db)
    session.commit()

    r = client.post(
        f"/prestamos/{prestamo['id']}/devolucion", headers=biblio_headers
    )
    assert r.status_code == 200
    assert r.json()["multa"] == 600


def test_no_se_puede_devolver_dos_veces(client, socio_id, libro_id, biblio_headers, login):
    prestamo = prestar(client, socio_id, libro_id, login("juan@example.com")).json()
    r = client.post(
        f"/prestamos/{prestamo['id']}/devolucion", headers=biblio_headers
    )
    assert r.status_code == 200
    r = client.post(
        f"/prestamos/{prestamo['id']}/devolucion", headers=biblio_headers
    )
    assert r.status_code == 409


def test_devolver_prestamo_inexistente(client, biblio_headers):
    r = client.post("/prestamos/999/devolucion", headers=biblio_headers)
    assert r.status_code == 404


def test_devolucion_requiere_bibliotecario(client, socio_id, libro_id, login):
    prestamo = prestar(client, socio_id, libro_id, login("juan@example.com")).json()
    r = client.post(
        f"/prestamos/{prestamo['id']}/devolucion", headers=login("juan@example.com")
    )
    assert r.status_code == 403


def test_prestamos_activos_del_socio(client, socio_id, libro_id, login, biblio_headers):
    headers = login("juan@example.com")
    p1 = prestar(client, socio_id, libro_id, headers).json()
    client.post(f"/prestamos/{p1['id']}/devolucion", headers=biblio_headers)

    r = client.get(
        f"/socios/{socio_id}/prestamos", params={"activos": True}, headers=headers
    )
    assert r.status_code == 200
    assert r.json() == []  # el unico prestamo ya fue devuelto

    r = client.get(f"/socios/{socio_id}/prestamos", headers=headers)
    assert len(r.json()) == 1  # historial completo


def test_socio_no_ve_prestamos_ajenos(client, biblio_headers, login):
    crear_socio(client, "juan@example.com")
    otro = crear_socio(client, "miradas@x.com").json()
    r = client.get(f"/socios/{otro['id']}/prestamos", headers=login("juan@example.com"))
    assert r.status_code == 403

    # el bibliotecario si puede ver los prestamos de cualquiera
    r = client.get(f"/socios/{otro['id']}/prestamos", headers=biblio_headers)
    assert r.status_code == 200


def test_token_expirado(client):
    from services.jwt import JWTService

    servicio = JWTService(
        "tup-2026-biblioteca-clave-super-secreta-larga-de-32-chars", expire_minutes=-1
    )
    token = servicio.create_access_token({"sub": "biblio@biblioteca.com"})
    r = client.get(
        "/socios/999/prestamos", headers={"Authorization": f"Bearer {token}"}
    )
    assert r.status_code == 401


def test_prestamos_de_socio_inexistente(client, biblio_headers):
    r = client.get("/socios/999/prestamos", headers=biblio_headers)
    assert r.status_code == 404
