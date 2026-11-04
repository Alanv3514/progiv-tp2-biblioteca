from typing import Annotated

from fastapi import Depends, Header, HTTPException, status
from sqlmodel import select

from database import SessionDep
from models.socio import ROL_BIBLIOTECARIO, Socio
from services.jwt import JWTService


def get_jwt_service() -> JWTService:
    return JWTService("tup-2026-biblioteca-clave-super-secreta-larga-de-32-chars")


JWTServiceDep = Annotated[JWTService, Depends(get_jwt_service)]


def get_socio_actual(
    session: SessionDep,
    jwt_service: JWTServiceDep,
    authorization: Annotated[str | None, Header()] = None,
) -> Socio:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Falta el header Authorization con Bearer",
        )
    token = authorization.removeprefix("Bearer ")
    payload = jwt_service.decode_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalido o expirado",
        )
    socio = session.exec(select(Socio).where(Socio.email == payload["sub"])).first()
    if socio is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Socio no encontrado"
        )
    return socio


SocioDep = Annotated[Socio, Depends(get_socio_actual)]


def requiere_rol(nombre_rol: str):
    def chequeo(socio: SocioDep) -> Socio:
        if socio.rol != nombre_rol:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requiere rol {nombre_rol}",
            )
        return socio

    return chequeo


BibliotecarioDep = Annotated[Socio, Depends(requiere_rol(ROL_BIBLIOTECARIO))]
