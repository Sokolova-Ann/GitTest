from pydantic import BaseModel


class TodoItem(BaseModel):
    """Модель для обновления задачи (без id)."""
    item: str

    class Config:
        schema_extra = {
            "example": {
                "item": "Обновлённый текст задачи"
            }
        }


class Todo(BaseModel):
    """Модель задачи: id + текст."""
    id: int
    item: str

    class Config:
        schema_extra = {
            "example": {
                "id": 1,
                "item": "Пример задачи для Swagger"
            }
        }

        