from sqlmodel import SQLModel, Field


class Autor(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    nombre: str
    nacionalidad: str | None = None


class AutorCreate(SQLModel):
    nombre: str
    nacionalidad: str | None = None


class AutorRead(SQLModel):
    id: int
    nombre: str
    nacionalidad: str | None = None
