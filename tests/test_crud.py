"""Tests del CRUD de autores, libros y socios (reglas 7 y 8)."""


def test_crear_y_obtener_autor(client):
    r = client.post("/autores", json={"nombre": "Autor", "nacionalidad": "AR"})
    assert r.status_code == 201
    autor = r.json()
    r = client.get(f"/autores/{autor['id']}")
    assert r.status_code == 200
    assert r.json()["nombre"] == "Autor"


def test_obtener_autor_inexistente(client):
    assert client.get("/autores/999").status_code == 404


def test_modificar_autor(client):
    r = client.post("/autores", json={"nombre": "Viejo", "nacionalidad": None})
    r = client.put(f"/autores/{r.json()['id']}", json={"nombre": "Nuevo", "nacionalidad": "BR"})
    assert r.status_code == 200
    assert r.json()["nombre"] == "Nuevo"


def test_eliminar_autor(client):
    r = client.post("/autores", json={"nombre": "Otro"})
    autor_id = r.json()["id"]
    r = client.delete(f"/autores/{autor_id}")
    assert r.status_code == 204
    # ya no existe
    assert client.get(f"/autores/{autor_id}").status_code == 404


# --- Libros ---


def crear_libro(client, isbn: str, stock: int = 2, titulo: str = "T"):
    return client.post(
        "/libros",
        json={"titulo": titulo, "isbn": isbn, "stock": stock, "anio": 2024},
    )


def test_crear_libro_y_consulta(client):
    r = crear_libro(client, "isbn-a", stock=5)
    assert r.status_code == 201
    libro = r.json()
    assert libro["stock"] == 5
    assert libro["autores"] == []

    r = client.get(f"/libros/{libro['id']}")
    assert r.status_code == 200


def test_isbn_duplicado_devuelve_409(client):
    crear_libro(client, "isbn-uniq")
    r = crear_libro(client, "isbn-uniq")
    assert r.status_code == 409


def test_isbn_duplicado_en_modificacion(client):
    crear_libro(client, "isbn-1")
    libro = crear_libro(client, "isbn-2").json()
    r = client.put(f"/libros/{libro['id']}", json={"isbn": "isbn-1"})
    assert r.status_code == 409


def test_stock_negativo_rechazado(client):
    r = crear_libro(client, "isbn-x", stock=-1)
    assert r.status_code == 422


def test_listar_libros_con_filtro_disponibles(client):
    crear_libro(client, "isbn-disp", stock=1, titulo="Disponible")
    crear_libro(client, "isbn-sinstock", stock=0, titulo="Sin stock")

    todos = client.get("/libros").json()
    assert len(todos) == 2

    disponibles = client.get("/libros", params={"disponibles": True}).json()
    assert [l["titulo"] for l in disponibles] == ["Disponible"]


def test_modificar_libro(client):
    libro = crear_libro(client, "isbn-m", stock=9).json()
    r = client.put(f"/libros/{libro['id']}", json={"titulo": "Renombrado", "stock": 4})
    assert r.status_code == 200
    assert r.json()["titulo"] == "Renombrado"
    assert r.json()["stock"] == 4


def test_eliminar_libro(client):
    libro = crear_libro(client, "isbn-del").json()
    assert client.delete(f"/libros/{libro['id']}").status_code == 204
    assert client.get(f"/libros/{libro['id']}").status_code == 404


def test_asociar_autor_a_libro(client):
    autor = client.post("/autores", json={"nombre": "Autor", "nacionalidad": None}).json()
    libro = crear_libro(client, "isbn-conautor").json()
    r = client.post(f"/libros/{libro['id']}/autores/{autor['id']}")
    assert r.status_code == 201
    r = client.get(f"/libros/{libro['id']}")
    assert r.json()["autores"][0]["nombre"] == "Autor"


def test_asociar_autor_inexistente_o_libro_inexistente(client):
    autor = client.post("/autores", json={"nombre": "Autor2", "nacionalidad": None}).json()
    libro = crear_libro(client, "isbn-y").json()
    assert client.post(f"/libros/{libro['id']}/autores/999").status_code == 404
    assert client.post(f"/libros/999/autores/{autor['id']}").status_code == 404


# --- Socios ---


def crear_socio(client, email: str):
    return client.post(
        "/socios", json={"nombre": "Nombre", "email": email}
    )


def test_crear_y_obtener_socio(client):
    r = crear_socio(client, "a@x.com")
    assert r.status_code == 201
    assert r.json()["activo"] is True
    assert client.get(f"/socios/{r.json()['id']}").status_code == 200


def test_email_duplicado_devuelve_409(client):
    crear_socio(client, "dup@x.com")
    assert crear_socio(client, "dup@x.com").status_code == 409


def test_email_duplicado_en_modificacion(client):
    crear_socio(client, "uno@x.com")
    socio = crear_socio(client, "dos@x.com").json()
    r = client.put(f"/socios/{socio['id']}", json={"email": "uno@x.com"})
    assert r.status_code == 409


def test_modificar_socio_desactivalo(client):
    socio = crear_socio(client, "b@x.com").json()
    r = client.put(f"/socios/{socio['id']}", json={"activo": False})
    assert r.status_code == 200
    assert r.json()["activo"] is False


def test_eliminar_socio(client):
    socio = crear_socio(client, "c@x.com").json()
    assert client.delete(f"/socios/{socio['id']}").status_code == 204
    assert client.get(f"/socios/{socio['id']}").status_code == 404


def test_recurso_inexistente_devuelve_404(client):
    assert client.get("/socios/999").status_code == 404
    assert client.get("/libros/999").status_code == 404
    assert client.put("/socios/999", json={"nombre": "x"}).status_code == 404
