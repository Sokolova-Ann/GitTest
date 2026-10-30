from typing import Optional, List
from sqlmodel import SQLModel, Field, Column, JSON
from pydantic import EmailStr


class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str
    password: str
    is_admin: bool = Field(default=False)   # ← новое поле
    events: Optional[List[int]] = Field(default=None, sa_column=Column(JSON))

    model_config = {
        "json_schema_extra": {
            "example": {
                "email": "user1@mail.ru",
                "password": "12345",
                "is_admin": False,
                "events": []
            }
        }
    }

class UserSignIn(SQLModel):
    email: str
    password: str

    model_config = {
        "json_schema_extra": {
            "example": {
                "email": "user1@mail.ru",
                "password": "12345"
            }
        }
    }