from datetime import datetime, timedelta

from fastapi import HTTPException, status
from sqlmodel import Session, select

from models.libro import Libro
from models.prestamo import Prestamo, PrestamoCreate
from models.socio import Socio

PLAZO_DIAS = 14
MULTA_POR_DIA = 100.0
LIMITE_PRESTAMOS_ACTIVOS = 3


def _cantidad_activos(session: Session, socio_id: int) -> int:
    return len(
        session.exec(
            select(Prestamo).where(
                Prestamo.socio_id == socio_id,
                Prestamo.fecha_devolucion == None,  # noqa: E711
            )
        ).all()
    )


def registrar_prestamo(session: Session, datos: PrestamoCreate) -> Prestamo:
    socio = session.get(Socio, datos.socio_id)
    if socio is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Socio no encontrado"
        )
    libro = session.get(Libro, datos.libro_id)
    if libro is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Libro no encontrado"
        )
    if not socio.activo:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Socio inactivo"
        )
    if _cantidad_activos(session, datos.socio_id) >= LIMITE_PRESTAMOS_ACTIVOS:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Socio ya tiene {LIMITE_PRESTAMOS_ACTIVOS} prestamos activos",
        )
    if libro.stock <= 0:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Libro sin stock disponible",
        )
    libro.stock -= 1
    ahora = datetime.now()
    prestamo = Prestamo(
        socio_id=socio.id,
        libro_id=libro.id,
        fecha_prestamo=ahora,
        fecha_vencimiento=ahora + timedelta(days=PLAZO_DIAS),
    )
    session.add(prestamo)
    session.commit()
    session.refresh(prestamo)
    return prestamo


def devolver_prestamo(session: Session, prestamo_id: int) -> Prestamo:
    prestamo = session.get(Prestamo, prestamo_id)
    if prestamo is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Prestamo no encontrado",
        )
    if prestamo.fecha_devolucion is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Prestamo ya devuelto",
        )
    ahora = datetime.now()
    dias_de_atraso = (ahora - prestamo.fecha_vencimiento).days
    prestamo.fecha_devolucion = ahora
    prestamo.multa = max(dias_de_atraso, 0) * MULTA_POR_DIA
    libro = session.get(Libro, prestamo.libro_id)
    if libro is not None:
        libro.stock += 1
    session.add(prestamo)
    session.commit()
    session.refresh(prestamo)
    return prestamo


def listar_prestamos_socio(
    session: Session, socio_id: int, activos: bool
) -> list[Prestamo]:
    socio = session.get(Socio, socio_id)
    if socio is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Socio no encontrado",
        )
    query = select(Prestamo).where(Prestamo.socio_id == socio_id)
    if activos:
        query = query.where(Prestamo.fecha_devolucion == None)  # noqa: E711
    return list(session.exec(query).all())
