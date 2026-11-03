from contextlib import asynccontextmanager
from fastapi import FastAPI
from database import create_tables


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_tables()
    yield


app = FastAPI(title="Biblioteca", lifespan=lifespan)


@app.get("/")
def read_root():
    return {"message": "API de biblioteca"}
