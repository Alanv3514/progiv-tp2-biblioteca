from fastapi import APIRouter, Depends, status
from sqlmodel import Session

from database import get_session
from models.prestamo import PrestamoCreate, PrestamoRead
from services import prestamos as prestamo_service

router = APIRouter(prefix="/prestamos", tags=["prestamos"])


@router.post("", response_model=PrestamoRead, status_code=status.HTTP_201_CREATED)
def registrar_prestamo(
    datos: PrestamoCreate, session: Session = Depends(get_session)
):
    prestamo = prestamo_service.registrar_prestamo(session, datos)
    return PrestamoRead.model_validate(prestamo)
