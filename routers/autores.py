from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from database import SessionDep
from dependencies import requiere_rol
from models.autor import Autor, AutorCreate, AutorRead
from models.socio import ROL_BIBLIOTECARIO

router = APIRouter(prefix="/autores", tags=["autores"])


@router.get("", response_model=list[AutorRead])
def listar_autores(session: SessionDep):
    autores = session.exec(select(Autor)).all()
    return [AutorRead.model_validate(a) for a in autores]


@router.get("/{id}", response_model=AutorRead)
def obtener_autor(id: int, session: SessionDep):
    autor = session.get(Autor, id)
    if autor is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Autor no encontrado"
        )
    return AutorRead.model_validate(autor)


@router.post(
    "",
    response_model=AutorRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(requiere_rol(ROL_BIBLIOTECARIO))],
)
def crear_autor(datos: AutorCreate, session: SessionDep):
    autor = Autor.model_validate(datos)
    session.add(autor)
    session.commit()
    session.refresh(autor)
    return AutorRead.model_validate(autor)


@router.put(
    "/{id}",
    response_model=AutorRead,
    dependencies=[Depends(requiere_rol(ROL_BIBLIOTECARIO))],
)
def modificar_autor(
    id: int, datos: AutorCreate, session: SessionDep
):
    autor = session.get(Autor, id)
    if autor is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Autor no encontrado"
        )
    autor.nombre = datos.nombre
    autor.nacionalidad = datos.nacionalidad
    session.add(autor)
    session.commit()
    session.refresh(autor)
    return AutorRead.model_validate(autor)


@router.delete(
    "/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(requiere_rol(ROL_BIBLIOTECARIO))],
)
def eliminar_autor(id: int, session: SessionDep):
    autor = session.get(Autor, id)
    if autor is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Autor no encontrado"
        )
    session.delete(autor)
    session.commit()
