from datetime import datetime
from sqlmodel import SQLModel, Field


class Prestamo(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    socio_id: int = Field(foreign_key="socio.id")
    libro_id: int = Field(foreign_key="libro.id")
    fecha_prestamo: datetime
    fecha_vencimiento: datetime
    fecha_devolucion: datetime | None = None
    multa: float = 0.0


class PrestamoCreate(SQLModel):
    socio_id: int
    libro_id: int


class PrestamoRead(SQLModel):
    id: int
    socio_id: int
    libro_id: int
    fecha_prestamo: datetime
    fecha_vencimiento: datetime
    fecha_devolucion: datetime | None = None
    multa: float
