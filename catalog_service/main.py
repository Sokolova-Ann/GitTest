from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from typing import List, Optional
from pydantic import BaseModel
from bson.errors import InvalidId
import datetime
from models import Film, Subscription, User, Friendship, WatchHistory
from database import init_db
from fastapi import FastAPI, HTTPException, Header, Depends

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield

app = FastAPI(title="Catalog Service", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

class AuthRequest(BaseModel):
    email: str
    password: str

class FilmCreate(BaseModel):
    title: str
    genre: str
    duration_sec: int
    rating: float
    poster_url: Optional[str] = None

@app.post("/users/register")
async def register(req: AuthRequest):
    if await User.find_one(User.email == req.email):
        raise HTTPException(status_code=400, detail="Email уже занят")
    user = User(email=req.email, password=req.password)
    await user.create()
    return {"message": "Успешная регистрация", "user_id": str(user.id)}

@app.post("/users/login")
async def login(req: AuthRequest):
    user = await User.find_one(User.email == req.email, User.password == req.password)
    if not user:
        raise HTTPException(status_code=401, detail="Неверный email или пароль")
    return {"message": "Вход выполнен", "user_id": str(user.id)}

@app.get("/users/{user_id}/subscription")
async def check_sub(user_id: str):
    sub = await Subscription.find_one(Subscription.user_id == user_id)
    return {"is_active": sub.is_active if sub else False}

@app.post("/users/{user_id}/subscribe")
async def subscribe(user_id: str):
    sub = await Subscription.find_one(Subscription.user_id == user_id)
    if not sub:
        sub = Subscription(user_id=user_id, is_active=True)
        await sub.create()
    else:
        sub.is_active = True
        await sub.save()
    return {"message": "Подписка оформлена"}

# --- ДРУЗЬЯ ---
@app.get("/users/{user_id}/friends", response_model=List[Friendship])
async def get_friends(user_id: str):
    return await Friendship.find(
        Friendship.user_id == user_id, 
        Friendship.status == "accepted"
    ).to_list()

@app.get("/users/{user_id}/friend_requests")
async def get_friend_requests(user_id: str):
    # Ищем заявки, где получатель - это user_id, а статус - pending
    reqs = await Friendship.find(
        Friendship.friend_id == user_id, 
        Friendship.status == "pending"
    ).to_list()
    
    result = []
    for req in reqs:
        # Находим того, кто отправил заявку
        sender = await User.get(req.user_id)
        if sender:
            result.append({
                "user_id": req.user_id,              # ID отправителя
                "friend_email": sender.email,        # Email отправителя
                "status": req.status
            })
    return result

@app.post("/users/{user_id}/friends")
async def add_friend(user_id: str, friend_email: str):
    friend = await User.find_one(User.email == friend_email)
    if not friend:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    if str(friend.id) == user_id:
        raise HTTPException(status_code=400, detail="Нельзя добавить себя")
    
    exists = await Friendship.find_one(Friendship.user_id == user_id, Friendship.friend_id == str(friend.id))
    if exists:
        raise HTTPException(status_code=400, detail="Заявка уже отправлена или вы уже друзья")
        
    new_f = Friendship(user_id=user_id, friend_id=str(friend.id), friend_email=friend.email, status="pending")
    await new_f.create()
    return {"message": "Заявка отправлена"}

@app.post("/users/{user_id}/friends/{friend_id}/accept")
async def accept_friend(user_id: str, friend_id: str):
    req = await Friendship.find_one(Friendship.user_id == friend_id, Friendship.friend_id == user_id, Friendship.status == "pending")
    if not req:
        raise HTTPException(status_code=404, detail="Заявка не найдена")
    
    req.status = "accepted"
    await req.save()
    
    sender = await User.get(friend_id)
    if sender:
        reverse_f = Friendship(user_id=user_id, friend_id=friend_id, friend_email=sender.email, status="accepted")
        await reverse_f.create()
        
    return {"message": "Теперь вы друзья"}

@app.delete("/users/{user_id}/friends/{friend_id}")
async def remove_friend(user_id: str, friend_id: str):
    await Friendship.find(Friendship.user_id == user_id, Friendship.friend_id == friend_id).delete()
    await Friendship.find(Friendship.user_id == friend_id, Friendship.friend_id == user_id).delete()
    return {"message": "Удалено"}

# --- ИСТОРИЯ ПРОСМОТРОВ ---
@app.post("/users/{user_id}/history")
async def save_history(user_id: str, film_id: str, position: int):
    film = await Film.get(film_id)
    title = film.title if film else "Неизвестный фильм"
    
    history = await WatchHistory.find_one(WatchHistory.user_id == user_id, WatchHistory.film_id == film_id)
    if history:
        history.last_position_sec = position
        history.watched_at = datetime.datetime.now(datetime.UTC)
        await history.save()
    else:
        new_h = WatchHistory(user_id=user_id, film_id=film_id, film_title=title, last_position_sec=position)
        await new_h.create()
    return {"message": "История сохранена"}

@app.get("/users/{user_id}/history")
async def get_history(user_id: str):
    return await WatchHistory.find(WatchHistory.user_id == user_id).sort(-WatchHistory.watched_at).to_list()

# --- ФИЛЬМЫ ---
@app.post("/films", response_model=Film)
async def add_film(data: FilmCreate):
    film = Film(**data.model_dump())
    await film.create()
    return film

@app.get("/films", response_model=List[Film])
async def get_films():
    return await Film.find_all().to_list()

@app.get("/films/{film_id}", response_model=Film)
async def get_film(film_id: str):
    try:
        film = await Film.get(film_id)
    except (InvalidId, TypeError):
        raise HTTPException(status_code=404, detail="Фильм не найден")
    if not film:
        raise HTTPException(status_code=404, detail="Фильм не найден")
    return film

@app.delete("/films/{film_id}")
async def delete_film(film_id: str):
    try:
        film = await Film.get(film_id)
    except (InvalidId, TypeError):
        raise HTTPException(status_code=404, detail="Фильм не найден")
        
    if not film:
        raise HTTPException(status_code=404, detail="Фильм не найден")
        
    await film.delete()
    return {"message": "Фильм успешно удален"}

# --- АДМИН ПАНЕЛЬ ---

# Секретный ключ для входа (в реальном проекте его хранят в .env)
ADMIN_TOKEN = "admin"

# Функция-зависимость для проверки токена
def verify_admin(x_admin_token: str = Header(None)):
    if x_admin_token != ADMIN_TOKEN:
        raise HTTPException(status_code=403, detail="Доступ запрещен: вы не администратор")
    return True

# Эндпоинт для получения списка всех пользователей (только для админа)
@app.get("/admin/users", dependencies=[Depends(verify_admin)])
async def get_all_users():
    users = await User.find_all().to_list()
    # Возвращаем без паролей
    return [{"id": str(u.id), "email": u.email} for u in users]

# Удаление фильма (теперь только для админа)
@app.delete("/admin/films/{film_id}", dependencies=[Depends(verify_admin)])
async def admin_delete_film(film_id: str):
    try:
        film = await Film.get(film_id)
    except (InvalidId, TypeError):
        raise HTTPException(status_code=404, detail="Фильм не найден")
    if not film:
        raise HTTPException(status_code=404, detail="Фильм не найден")
    await film.delete()
    return {"message": "Фильм удален"}

# Выдача подписки пользователю вручную (если он заплатил наличными, например)
@app.post("/admin/users/{user_id}/give_sub", dependencies=[Depends(verify_admin)])
async def admin_give_sub(user_id: str):
    sub = await Subscription.find_one(Subscription.user_id == user_id)
    if not sub:
        sub = Subscription(user_id=user_id, is_active=True)
        await sub.create()
    else:
        sub.is_active = True
        await sub.save()
    return {"message": "Подписка выдана"}