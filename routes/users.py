from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import select

from database.connection import get_session
from models.users import User, UserSignIn

user_router = APIRouter(tags=["User"])


@user_router.post("/signup")
async def sign_user_up(user: User, session=Depends(get_session)) -> dict:
    statement = select(User).where(User.email == user.email)
    user_exist = session.exec(statement).first()
    if user_exist:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Пользователь с таким email уже существует"
        )
    session.add(user)
    session.commit()
    session.refresh(user)
    return {"message": "Пользователь успешно зарегистрирован"}


@user_router.post("/signin")
async def sign_user_in(user: UserSignIn, session=Depends(get_session)) -> dict:
    statement = select(User).where(User.email == user.email)
    user_exist = session.exec(statement).first()
    if not user_exist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь с таким email не найден"
        )
    if user_exist.password == user.password:
        return {"message": "Вход выполнен успешно"}
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Неверные учётные данные"
    )