from fastapi import APIRouter, Depends, status

from database import SessionDep
from dependencies import requiere_rol, SocioDep
from models.prestamo import PrestamoCreate, PrestamoRead
from models.socio import ROL_BIBLIOTECARIO
from services import prestamos as prestamo_service

router = APIRouter(prefix="/prestamos", tags=["prestamos"])


@router.post("", response_model=PrestamoRead, status_code=status.HTTP_201_CREATED)
def registrar_prestamo(datos: PrestamoCreate, session: SessionDep, actual: SocioDep):
    prestamo = prestamo_service.registrar_prestamo(session, datos, actual)
    return PrestamoRead.model_validate(prestamo)


@router.post(
    "/{id}/devolucion",
    response_model=PrestamoRead,
    dependencies=[Depends(requiere_rol(ROL_BIBLIOTECARIO))],
)
def devolver_prestamo(id: int, session: SessionDep):
    prestamo = prestamo_service.devolver_prestamo(session, id)
    return PrestamoRead.model_validate(prestamo)
