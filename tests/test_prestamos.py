"""Tests de reglas de negocio de prestamos (reglas 1 a 6)."""

from datetime import datetime, timedelta


def prestar(client, socio_id: int, libro_id: int):
    return client.post(
        "/prestamos", json={"socio_id": socio_id, "libro_id": libro_id}
    )


def test_prestamo_feliz(client, socio_id, libro_id):
    r = prestar(client, socio_id, libro_id)
    assert r.status_code == 201
    prestamo = r.json()
    prestado = datetime.fromisoformat(prestamo["fecha_prestamo"])
    venc = datetime.fromisoformat(prestamo["fecha_vencimiento"])
    assert venc - prestado == timedelta(days=14)
    assert prestamo["fecha_devolucion"] is None
    assert prestamo["multa"] == 0
    assert client.get(f"/libros/{libro_id}").json()["stock"] == 2  # 3 - 1


def test_socio_no_inexistente_y_libro_inexistente(client, libro_id):
    assert prestar(client, 999, libro_id).status_code == 404
    # socio valido, libro inexistente
    socio = client.post("/socios", json={"nombre": "S", "email": "s@x.com"}).json()
    assert prestar(client, socio["id"], 999).status_code == 404


def test_socio_inactivo_no_puede_prestar(client, libro_id):
    socio = client.post(
        "/socios", json={"nombre": "Inactivo", "email": "i@x.com", "activo": False}
    ).json()
    r = prestar(client, socio["id"], libro_id)
    assert r.status_code == 403


def test_max_tres_prestamos_activos(client, libro_id):
    socio = client.post("/socios", json={"nombre": "V", "email": "v@x.com"}).json()
    for _ in range(3):
        assert prestar(client, socio["id"], libro_id).status_code == 201
    r = prestar(client, socio["id"], libro_id)
    assert r.status_code == 409


def test_libro_sin_stock(client, socio_id):
    libro = client.post(
        "/libros",
        json={"titulo": "NoStock", "isbn": "ns", "stock": 0, "anio": 2024},
    ).json()
    r = prestar(client, socio_id, libro["id"])
    assert r.status_code == 409


def test_prestamo_descuenta_stock(client, socio_id, libro_id):
    prestar(client, socio_id, libro_id)
    r = client.get(f"/libros/{libro_id}")
    assert r.json()["stock"] == 2  # 3 - 1


def test_devolucion_a_tiempo(client, socio_id, libro_id):
    prestamo = prestar(client, socio_id, libro_id).json()
    stock_antes = client.get(f"/libros/{libro_id}").json()["stock"]
    r = client.post(f"/prestamos/{prestamo['id']}/devolucion")
    assert r.status_code == 200
    devuelto = r.json()
    assert devuelto["multa"] == 0
    assert devuelto["fecha_devolucion"] is not None
    # repone stock
    assert client.get(f"/libros/{libro_id}").json()["stock"] == stock_antes + 1


def test_devolucion_con_atraso_aplica_multa(client, socio_id, libro_id, session):
    prestamo = prestar(client, socio_id, libro_id).json()

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

    r = client.post(f"/prestamos/{prestamo['id']}/devolucion")
    assert r.status_code == 200
    assert r.json()["multa"] == 600


def test_no_se_puede_devolver_dos_veces(client, socio_id, libro_id):
    prestamo = prestar(client, socio_id, libro_id).json()
    assert client.post(f"/prestamos/{prestamo['id']}/devolucion").status_code == 200
    r = client.post(f"/prestamos/{prestamo['id']}/devolucion")
    assert r.status_code == 409


def test_devolver_prestamo_inexistente(client):
    assert client.post("/prestamos/999/devolucion").status_code == 404


def test_prestamos_activos_del_socio(client, socio_id, libro_id):
    p1 = prestar(client, socio_id, libro_id).json()
    client.post(
        f"/prestamos/{p1['id']}/devolucion"
    )

    r = client.get(f"/socios/{socio_id}/prestamos", params={"activos": True})
    assert r.status_code == 200
    assert r.json() == []  # el unico prestamo ya fue devuelto

    r = client.get(f"/socios/{socio_id}/prestamos")
    assert len(r.json()) == 1  # historial completo


def test_prestamos_de_socio_inexistente(client):
    r = client.get("/socios/999/prestamos")
    assert r.status_code == 404
