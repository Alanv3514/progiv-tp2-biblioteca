from fastapi import FastAPI

app = FastAPI(title="Biblioteca")


@app.get("/")
def read_root():
    return {"message": "API de biblioteca"}
