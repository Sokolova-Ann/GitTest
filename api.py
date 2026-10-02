from fastapi import FastAPI
from todo import todo_router

app = FastAPI(
    title="Todo API — Практическое занятие №4",
    description="Приложение для управления списком задач на FastAPI.",
    version="1.0.0"
)


@app.get("/", summary="Приветствие")
async def welcome() -> dict:
    return {
        "message": "Привет!"
    }

app.include_router(todo_router)
