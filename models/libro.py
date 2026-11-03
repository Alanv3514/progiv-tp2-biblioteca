from sqlmodel import SQLModel, Field
from models.autor import AutorRead


class Libro(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    titulo: str
    isbn: str = Field(unique=True)
    stock: int
    anio: int


class LibroCreate(SQLModel):
    titulo: str
    isbn: str
    stock: int = Field(ge=0)
    anio: int


class LibroUpdate(SQLModel):
    titulo: str | None = None
    isbn: str | None = None
    stock: int | None = Field(default=None, ge=0)
    anio: int | None = None


class LibroRead(SQLModel):
    id: int
    titulo: str
    isbn: str
    stock: int
    anio: int
    autores: list[AutorRead] = []
