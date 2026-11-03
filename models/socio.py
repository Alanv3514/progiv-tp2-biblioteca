from sqlmodel import SQLModel, Field


class Socio(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    nombre: str
    email: str = Field(unique=True)
    activo: bool = True


class SocioCreate(SQLModel):
    nombre: str
    email: str
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
