from typing import Annotated

from fastapi import Depends
from sqlmodel import SQLModel, create_engine, Session

# check_same_thread=False only needed for SQLite
engine = create_engine(
    "sqlite:///./database.db",
    connect_args={"check_same_thread": False},
)


def create_tables() -> None:
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session


SessionDep = Annotated[Session, Depends(get_session)]
