from contextlib import asynccontextmanager
from fastapi import FastAPI
from database import create_tables
from routers import autores, libros, socios


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_tables()
    yield


app = FastAPI(title="Biblioteca", lifespan=lifespan)

app.include_router(autores.router)
app.include_router(libros.router)
app.include_router(socios.router)


@app.get("/")
def read_root():
    return {"message": "API de biblioteca"}
