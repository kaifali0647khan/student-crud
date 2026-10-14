from contextlib import asynccontextmanager

from fastapi import FastAPI

from .database import init_db
from .routes_ai import router as ai_router
from .routes_students import router as students_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()  # create the table on startup if it doesn't exist
    yield


app = FastAPI(
    title="Students Database CRUD API",
    description="EWB internship project: FastAPI + SQLite, with an optional Ollama AI extension.",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(students_router)
app.include_router(ai_router)


@app.get("/", tags=["Health"])
def root():
    return {"message": "Students API is running", "docs": "/docs"}
