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
    stock: int
    anio: int


class LibroRead(SQLModel):
    id: int
    titulo: str
    isbn: str
    stock: int
    anio: int
    autores: list[AutorRead] = []
