from fastapi import FastAPI
from contextlib import asynccontextmanager
from database import init_db
from models import User
from routes import router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- Запуск ---
    print("Подключение к MongoDB...")
    await init_db()
    
    # Создаем админа по умолчанию
    admin = await User.find_one(User.email == "admin@test.com")
    if not admin:
        admin = User(email="admin@test.com", password="admin123", is_admin=True)
        await admin.create()
        print("Создан админ: admin@test.com / admin123")
        
    yield
    # --- Остановка ---
    print("Отключение от MongoDB...")

app = FastAPI(lifespan=lifespan, title="Todo App - MongoDB")
app.include_router(router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8080, reload=True)