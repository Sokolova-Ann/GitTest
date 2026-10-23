from fastapi import APIRouter, HTTPException, status
from models.users import NewUser, UserSignIn
from database.connection import users_db

user_router = APIRouter(tags=["User"])


@user_router.post("/signup")
async def sign_new_user(data: NewUser) -> dict:
    if data.email in users_db:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Пользователь с таким email уже существует"
        )
    users_db[data.email] = data
    return {"message": "Пользователь успешно зарегистрирован!"}


@user_router.post("/signin")
async def sign_user_in(user: UserSignIn) -> dict:
    if user.email not in users_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден"
        )
    if users_db[user.email].password != user.password:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Неверные учётные данные"
        )
    return {"message": "Вход выполнен успешно"}