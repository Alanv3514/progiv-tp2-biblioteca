from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from database import get_session
from models.prestamo import PrestamoRead
from models.socio import Socio, SocioCreate, SocioRead, SocioUpdate
from services import prestamos as prestamo_service

router = APIRouter(prefix="/socios", tags=["socios"])


def _email_duplicado(session: Session, email: str, socio_id: int | None = None) -> bool:
    socio = session.exec(select(Socio).where(Socio.email == email)).first()
    return socio is not None and socio.id != socio_id


@router.get("", response_model=list[SocioRead])
def listar_socios(session: Session = Depends(get_session)):
    socios = session.exec(select(Socio)).all()
    return [SocioRead.model_validate(s) for s in socios]


@router.get("/{id}", response_model=SocioRead)
def obtener_socio(id: int, session: Session = Depends(get_session)):
    socio = session.get(Socio, id)
    if socio is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Socio no encontrado"
        )
    return SocioRead.model_validate(socio)


@router.post("", response_model=SocioRead, status_code=status.HTTP_201_CREATED)
def crear_socio(datos: SocioCreate, session: Session = Depends(get_session)):
    if _email_duplicado(session, datos.email):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Email ya registrado"
        )
    socio = Socio.model_validate(datos)
    session.add(socio)
    session.commit()
    session.refresh(socio)
    return SocioRead.model_validate(socio)


@router.put("/{id}", response_model=SocioRead)
def modificar_socio(
    id: int, datos: SocioUpdate, session: Session = Depends(get_session)
):
    socio = session.get(Socio, id)
    if socio is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Socio no encontrado"
        )
    cambios = datos.model_dump(exclude_unset=True)
    if "email" in cambios and _email_duplicado(session, cambios["email"], socio.id):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Email ya registrado"
        )
    for campo, valor in cambios.items():
        setattr(socio, campo, valor)
    session.add(socio)
    session.commit()
    session.refresh(socio)
    return SocioRead.model_validate(socio)


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_socio(id: int, session: Session = Depends(get_session)):
    socio = session.get(Socio, id)
    if socio is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Socio no encontrado"
        )
    session.delete(socio)
    session.commit()


@router.get("/{id}/prestamos", response_model=list[PrestamoRead])
def prestamos_socio(
    id: int,
    activos: bool | None = None,
    session: Session = Depends(get_session),
):
    prestamos = prestamo_service.listar_prestamos_socio(
        session, id, activos if activos is not None else False
    )
    return [PrestamoRead.model_validate(p) for p in prestamos]
