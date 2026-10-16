from fastapi import FastAPI
from todo import todo_router

app = FastAPI()

app.include_router(todo_router)


@app.get("/ping")
async def ping():
    return {"status": "ok"}

