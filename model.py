from typing import List, Optional
from pydantic import BaseModel
from fastapi import Form


class Todo(BaseModel):
    id: Optional[int] = None
    item: str

    @classmethod
    def as_form(cls, item: str = Form(...)):
        return cls(item=item)

    model_config = {
        "json_schema_extra": {
            "example": {
                "id": 1,
                "item": "Прочитать главу книги по FastAPI"
            }
        }
    }


class TodoItem(BaseModel):
    item: str

    model_config = {
        "json_schema_extra": {
            "example": {"item": "Прочитать главу книги по FastAPI"}
        }
    }


class TodoItems(BaseModel):
    todos: List[TodoItem]

    model_config = {
        "json_schema_extra": {
            "example": {
                "todos": [
                    {"item": "Задача 1"},
                    {"item": "Задача 2"}
                ]
            }
        }
    }

    