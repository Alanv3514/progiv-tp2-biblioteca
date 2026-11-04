"""Tests del CRUD de autores, libros y socios (reglas 7 y 8)."""


def test_raiz(client):
    r = client.get("/")
    assert r.status_code == 200
    assert r.json() == {"message": "API de biblioteca"}


def crear_socio(client, email: str):
    return client.post(
        "/socios", json={"nombre": "Nombre", "email": email, "password": "1234"}
    )


def crear_libro(client, isbn: str, stock: int = 2, titulo: str = "T", headers=None):
    return client.post(
        "/libros",
        json={"titulo": titulo, "isbn": isbn, "stock": stock, "anio": 2024},
        headers=headers,
    )


# --- Catalogo: requiere bibliotecario ---


def test_catalogo_sin_token_devuelve_401(client):
    assert client.post("/libros", json={}).status_code == 401
    assert (
        client.post("/autores", json={"nombre": "A", "nacionalidad": None}).status_code
        == 401
    )


def test_catalogo_con_socio_devuelve_403(client, biblio_headers, login):
    crear_socio(client, "socio403@x.com")
    r = crear_libro(client, "isbn-socio", headers=login("socio403@x.com"))
    assert r.status_code == 403


# --- Autores ---


def test_crear_y_obtener_autor(client, biblio_headers):
    r = client.post(
        "/autores", json={"nombre": "Autor", "nacionalidad": "AR"}, headers=biblio_headers
    )
    assert r.status_code == 201
    autor = r.json()
    r = client.get(f"/autores/{autor['id']}")
    assert r.status_code == 200
    assert r.json()["nombre"] == "Autor"


def test_obtener_autor_inexistente(client):
    assert client.get("/autores/999").status_code == 404


def test_modificar_autor(client, biblio_headers):
    r = client.post(
        "/autores", json={"nombre": "Viejo", "nacionalidad": None}, headers=biblio_headers
    )
    r = client.put(
        f"/autores/{r.json()['id']}",
        json={"nombre": "Nuevo", "nacionalidad": "BR"},
        headers=biblio_headers,
    )
    assert r.status_code == 200
    assert r.json()["nombre"] == "Nuevo"


def test_eliminar_autor(client, biblio_headers):
    r = client.post(
        "/autores", json={"nombre": "Otro", "nacionalidad": None}, headers=biblio_headers
    )
    autor_id = r.json()["id"]
    r = client.delete(f"/autores/{autor_id}", headers=biblio_headers)
    assert r.status_code == 204
    # ya no existe
    assert client.get(f"/autores/{autor_id}").status_code == 404


# --- Libros ---


def test_crear_libro_y_consulta(client, biblio_headers):
    r = crear_libro(client, "isbn-a", stock=5, headers=biblio_headers)
    assert r.status_code == 201
    libro = r.json()
    assert libro["stock"] == 5
    assert libro["autores"] == []

    r = client.get(f"/libros/{libro['id']}")
    assert r.status_code == 200


def test_isbn_duplicado_devuelve_409(client, biblio_headers):
    crear_libro(client, "isbn-uniq", headers=biblio_headers)
    r = crear_libro(client, "isbn-uniq", headers=biblio_headers)
    assert r.status_code == 409


def test_isbn_duplicado_en_modificacion(client, biblio_headers):
    crear_libro(client, "isbn-1", headers=biblio_headers)
    libro = crear_libro(client, "isbn-2", headers=biblio_headers).json()
    r = client.put(
        f"/libros/{libro['id']}", json={"isbn": "isbn-1"}, headers=biblio_headers
    )
    assert r.status_code == 409


def test_stock_negativo_rechazado(client, biblio_headers):
    r = crear_libro(client, "isbn-x", stock=-1, headers=biblio_headers)
    assert r.status_code == 422


def test_listar_libros_con_filtro_disponibles(client, biblio_headers):
    crear_libro(client, "isbn-disp", stock=1, titulo="Disponible", headers=biblio_headers)
    crear_libro(client, "isbn-sinstock", stock=0, titulo="Sin stock", headers=biblio_headers)

    todos = client.get("/libros").json()
    assert len(todos) == 2

    disponibles = client.get("/libros", params={"disponibles": True}).json()
    assert [libro["titulo"] for libro in disponibles] == ["Disponible"]


def test_modificar_libro(client, biblio_headers):
    libro = crear_libro(client, "isbn-m", stock=9, headers=biblio_headers).json()
    r = client.put(
        f"/libros/{libro['id']}",
        json={"titulo": "Renombrado", "stock": 4},
        headers=biblio_headers,
    )
    assert r.status_code == 200
    assert r.json()["titulo"] == "Renombrado"
    assert r.json()["stock"] == 4


def test_eliminar_libro(client, biblio_headers):
    libro = crear_libro(client, "isbn-del", headers=biblio_headers).json()
    r = client.delete(f"/libros/{libro['id']}", headers=biblio_headers)
    assert r.status_code == 204
    assert client.get(f"/libros/{libro['id']}").status_code == 404


def test_asociar_autor_a_libro(client, biblio_headers):
    autor = client.post(
        "/autores",
        json={"nombre": "Autor", "nacionalidad": None},
        headers=biblio_headers,
    ).json()
    libro = crear_libro(client, "isbn-conautor", headers=biblio_headers).json()
    r = client.post(
        f"/libros/{libro['id']}/autores/{autor['id']}", headers=biblio_headers
    )
    assert r.status_code == 201
    r = client.get(f"/libros/{libro['id']}")
    assert r.json()["autores"][0]["nombre"] == "Autor"


def test_asociar_autor_inexistente_o_libro_inexistente(client, biblio_headers):
    autor = client.post(
        "/autores",
        json={"nombre": "Autor2", "nacionalidad": None},
        headers=biblio_headers,
    ).json()
    libro = crear_libro(client, "isbn-y", headers=biblio_headers).json()
    r = client.post(f"/libros/{libro['id']}/autores/999", headers=biblio_headers)
    assert r.status_code == 404
    r = client.post(f"/libros/999/autores/{autor['id']}", headers=biblio_headers)
    assert r.status_code == 404


# --- Socios ---


def test_crear_y_obtener_socio(client):
    r = crear_socio(client, "a@x.com")
    assert r.status_code == 201
    assert r.json()["activo"] is True
    assert client.get(f"/socios/{r.json()['id']}").status_code == 200


def test_email_duplicado_devuelve_409(client):
    crear_socio(client, "dup@x.com")
    assert crear_socio(client, "dup@x.com").status_code == 409


def test_email_duplicado_en_modificacion(client, biblio_headers):
    crear_socio(client, "uno@x.com")
    socio = crear_socio(client, "dos@x.com").json()
    r = client.put(
        f"/socios/{socio['id']}",
        json={"email": "uno@x.com"},
        headers=biblio_headers,
    )
    assert r.status_code == 409


def test_modificar_socio_desactivarlo(client, biblio_headers):
    socio = crear_socio(client, "b@x.com").json()
    r = client.put(
        f"/socios/{socio['id']}", json={"activo": False}, headers=biblio_headers
    )
    assert r.status_code == 200
    assert r.json()["activo"] is False


def test_eliminar_socio(client, biblio_headers):
    socio = crear_socio(client, "c@x.com").json()
    assert client.delete(f"/socios/{socio['id']}", headers=biblio_headers).status_code == 204
    assert client.get(f"/socios/{socio['id']}").status_code == 404


def test_recurso_inexistente_devuelve_404(client, biblio_headers):
    assert client.get("/socios/999").status_code == 404
    assert client.get("/libros/999").status_code == 404
    r = client.put("/socios/999", json={"nombre": "x"}, headers=biblio_headers)
    assert r.status_code == 404


# --- Listados ---


def test_listar_autores(client, biblio_headers):
    client.post(
        "/autores", json={"nombre": "Listado", "nacionalidad": None}, headers=biblio_headers
    )
    r = client.get("/autores")
    assert r.status_code == 200
    assert len(r.json()) == 1


def test_listar_socios(client):
    crear_socio(client, "list@x.com")
    r = client.get("/socios")
    assert r.status_code == 200
    # el bibliotecario sembrado + el socio creado por este test
    assert len(r.json()) == 2


# --- Recurso inexistente en PUT y DELETE ---


def test_put_y_delete_autor_inexistente(client, biblio_headers):
    r = client.put(
        "/autores/999", json={"nombre": "x", "nacionalidad": None}, headers=biblio_headers
    )
    assert r.status_code == 404
    r = client.delete("/autores/999", headers=biblio_headers)
    assert r.status_code == 404


def test_put_y_delete_libro_inexistente(client, biblio_headers):
    r = client.put("/libros/999", json={"titulo": "x"}, headers=biblio_headers)
    assert r.status_code == 404
    r = client.delete("/libros/999", headers=biblio_headers)
    assert r.status_code == 404


def test_eliminar_socio_inexistente(client, biblio_headers):
    r = client.delete("/socios/999", headers=biblio_headers)
    assert r.status_code == 404


# --- Eliminacion de libro con autores asociados ---


def test_eliminar_libro_con_autores_asociados(client, biblio_headers):
    autor = client.post(
        "/autores", json={"nombre": "A", "nacionalidad": None}, headers=biblio_headers
    ).json()
    libro = crear_libro(client, "isbn-eliminar", headers=biblio_headers).json()
    client.post(f"/libros/{libro['id']}/autores/{autor['id']}", headers=biblio_headers)

    r = client.delete(f"/libros/{libro['id']}", headers=biblio_headers)
    assert r.status_code == 204
    # el autor sobrevive aunque el libro se haya ido
    assert client.get(f"/autores/{autor['id']}").status_code == 200


# --- database ---


def test_get_session_funciona(engine, monkeypatch):
    import database

    monkeypatch.setattr(database, "engine", engine)
    generador = database.get_session()
    sesion = next(generador)
    generador.close()

    from sqlmodel import Session

    assert isinstance(sesion, Session)


def test_seed_bibliotecario_es_idempotente(engine, monkeypatch):
    import database
    import main
    from models.socio import ROL_BIBLIOTECARIO, Socio
    from sqlmodel import Session, select

    monkeypatch.setattr(database, "engine", engine)
    main.sembrar_bibliotecario()
    main.sembrar_bibliotecario()

    with Session(engine) as session:
        biblios = session.exec(
            select(Socio).where(Socio.rol == ROL_BIBLIOTECARIO)
        ).all()
        assert len(biblios) == 1
