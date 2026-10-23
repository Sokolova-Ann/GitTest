from typing import Optional, List
from pydantic import BaseModel, EmailStr
from models.events import Event


class User(BaseModel):
    email: EmailStr
    password: str
    events: Optional[List[Event]] = None

    model_config = {
        "json_schema_extra": {
            "example": {
                "email": "fastapi@packt.com",
                "password": "Stro0ng!",
                "events": []
            }
        }
    }


class NewUser(User):
    """Модель для регистрации. Наследуется от User."""
    pass


class UserSignIn(BaseModel):
    email: EmailStr
    password: str

    model_config = {
        "json_schema_extra": {
            "example": {
                "email": "fastapi@packt.com",
                "password": "Stro0ng!"
            }
        }
    }