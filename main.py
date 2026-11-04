from sqlmodel import Session, select

from fastapi import FastAPI

import database
from database import create_tables
from models.socio import ROL_BIBLIOTECARIO, Socio
from routers import autores, libros, prestamos, socios, login
from utils.hash import hash_password


app = FastAPI(title="Biblioteca")

app.include_router(login.router)
app.include_router(autores.router)
app.include_router(libros.router)
app.include_router(socios.router)
app.include_router(prestamos.router)


def sembrar_bibliotecario():
    # el bibliotecario queda sembrado la primera vez: biblio@biblioteca.com / 123
    with Session(database.engine) as session:
        ya_hay = session.exec(
            select(Socio).where(Socio.rol == ROL_BIBLIOTECARIO)
        ).first()
        if ya_hay:
            return
        session.add(
            Socio(
                nombre="Bibliotecario de turno",
                email="biblio@biblioteca.com",
                password=hash_password("1234"),
                rol=ROL_BIBLIOTECARIO,
            )
        )
        session.commit()


@app.on_event("startup")
def on_startup():
    create_tables()
    sembrar_bibliotecario()


@app.get("/")
def read_root():
    return {"message": "API de biblioteca"}
