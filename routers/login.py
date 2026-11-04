from fastapi import APIRouter, HTTPException, status
from sqlmodel import select

from database import SessionDep
from dependencies import JWTServiceDep
from models.socio import LoginRequest, LoginResponse, Socio
from utils.hash import verify_password

router = APIRouter(tags=["auth"])


@router.post("/login", response_model=LoginResponse)
def login(datos: LoginRequest, session: SessionDep, jwt_service: JWTServiceDep):
    socio = session.exec(select(Socio).where(Socio.email == datos.email)).first()
    if socio is None or not verify_password(datos.password, socio.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email o password incorrecto",
        )
    return LoginResponse(
        msg="ok", token=jwt_service.create_access_token({"sub": socio.email})
    )
