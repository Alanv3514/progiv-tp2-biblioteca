from sqlmodel import SQLModel, Field


class LibroAutor(SQLModel, table=True):
    libro_id: int = Field(foreign_key="libro.id", primary_key=True)
    autor_id: int = Field(foreign_key="autor.id", primary_key=True)
