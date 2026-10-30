from fastapi import FastAPI
from fastapi.responses import RedirectResponse

from database.connection import conn
from routes.users import user_router
from routes.events import event_router
from routes.admin import admin_router

app = FastAPI()

app.include_router(user_router, prefix="/user")
app.include_router(event_router, prefix="/event")
app.include_router(admin_router)  # префикс /admin уже внутри


@app.on_event("startup")
def on_startup():
    conn()


@app.get("/")
async def home():
    return RedirectResponse(url="/admin/login")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8080, reload=True)