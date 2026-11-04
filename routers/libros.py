from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from database import SessionDep
from dependencies import requiere_rol
from models.autor import Autor, AutorRead
from models.libro import Libro, LibroCreate, LibroRead, LibroUpdate
from models.libro_autor import LibroAutor
from models.socio import ROL_BIBLIOTECARIO

BIBLIOTECARIO = [Depends(requiere_rol(ROL_BIBLIOTECARIO))]

router = APIRouter(prefix="/libros", tags=["libros"])


def _libro_read(session: Session, libro: Libro) -> LibroRead:
    assert libro.id is not None
    # autores se resuelven en la tabla de asociacion para evitar lazy loading
    autores = session.exec(
        select(Autor)
        .join(LibroAutor, LibroAutor.autor_id == Autor.id)  # type: ignore[arg-type]
        .where(LibroAutor.libro_id == libro.id)
    ).all()
    return LibroRead(
        id=libro.id,
        titulo=libro.titulo,
        isbn=libro.isbn,
        stock=libro.stock,
        anio=libro.anio,
        autores=[AutorRead.model_validate(a) for a in autores],
    )


def _isbn_duplicado(session: Session, isbn: str, libro_id: int | None = None) -> bool:
    libro = session.exec(select(Libro).where(Libro.isbn == isbn)).first()
    return libro is not None and libro.id != libro_id


@router.get("", response_model=list[LibroRead])
def listar_libros(
    session: SessionDep, disponibles: bool | None = None
):
    query = select(Libro)
    if disponibles:
        query = query.where(Libro.stock > 0)
    return [_libro_read(session, un_libro) for un_libro in session.exec(query).all()]


@router.get("/{id}", response_model=LibroRead)
def obtener_libro(id: int, session: SessionDep):
    libro = session.get(Libro, id)
    if libro is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Libro no encontrado"
        )
    return _libro_read(session, libro)


@router.post(
    "",
    response_model=LibroRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=BIBLIOTECARIO,
)
def crear_libro(datos: LibroCreate, session: SessionDep):
    if _isbn_duplicado(session, datos.isbn):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="ISBN ya registrado"
        )
    libro = Libro.model_validate(datos)
    session.add(libro)
    session.commit()
    session.refresh(libro)
    return _libro_read(session, libro)


@router.put("/{id}", response_model=LibroRead, dependencies=BIBLIOTECARIO)
def modificar_libro(
    id: int, datos: LibroUpdate, session: SessionDep
):
    libro = session.get(Libro, id)
    if libro is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Libro no encontrado"
        )
    cambios = datos.model_dump(exclude_unset=True)
    if "isbn" in cambios and _isbn_duplicado(session, cambios["isbn"], libro.id):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="ISBN ya registrado"
        )
    for campo, valor in cambios.items():
        setattr(libro, campo, valor)
    session.add(libro)
    session.commit()
    session.refresh(libro)
    return _libro_read(session, libro)


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=BIBLIOTECARIO)
def eliminar_libro(id: int, session: SessionDep):
    libro = session.get(Libro, id)
    if libro is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Libro no encontrado"
        )
    for vinculo in session.exec(
        select(LibroAutor).where(LibroAutor.libro_id == id)
    ).all():
        session.delete(vinculo)
    session.delete(libro)
    session.commit()


@router.post(
    "/{id}/autores/{autor_id}",
    response_model=LibroRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=BIBLIOTECARIO,
)
def asociar_autor(
    id: int, autor_id: int, session: SessionDep
):
    libro = session.get(Libro, id)
    if libro is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Libro no encontrado"
        )
    autor = session.get(Autor, autor_id)
    if autor is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Autor no encontrado"
        )
    assert libro.id is not None and autor.id is not None
    vinculo = session.get(LibroAutor, (libro.id, autor.id))
    if vinculo is None:
        session.add(LibroAutor(libro_id=libro.id, autor_id=autor.id))
        session.commit()
    return _libro_read(session, libro)
