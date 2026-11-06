from typing import Optional, List
from beanie import Document
from pydantic import BaseModel, EmailStr
from typing import Optional # не забудьте добавить импорт, если его нет

class Todo(Document):
    item: str
    is_done: bool = False
    owner_email: Optional[str] = None  # <-- Сделали необязательным

    class Settings:
        name = "todos"

    model_config = {
        "json_schema_extra": {
            "example": {"item": "Купить хлеб", "is_done": False, "owner_email": "user@test.com"}
        }
    }

class User(Document):
    email: EmailStr
    password: str
    is_admin: bool = False

    class Settings:
        name = "users"

    model_config = {
        "json_schema_extra": {
            "example": {"email": "admin@test.com", "password": "admin123", "is_admin": True}
        }
    }

class UserSignIn(BaseModel):
    email: EmailStr
    password: str