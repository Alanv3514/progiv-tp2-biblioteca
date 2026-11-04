from sqlmodel import SQLModel, Field

ROL_BIBLIOTECARIO = "bibliotecario"
ROL_SOCIO = "socio"


class Socio(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    nombre: str
    email: str = Field(unique=True)
    password: str = Field(min_length=4, max_length=72)
    activo: bool = True
    rol: str = ROL_SOCIO


class SocioCreate(SQLModel):
    nombre: str
    email: str
    password: str
    activo: bool = True


class SocioUpdate(SQLModel):
    nombre: str | None = None
    email: str | None = None
    activo: bool | None = None


class SocioRead(SQLModel):
    id: int
    nombre: str
    email: str
    activo: bool
    rol: str


class LoginRequest(SQLModel):
    email: str
    password: str


class LoginResponse(SQLModel):
    msg: str
    token: str
