from typing import List
from pydantic import BaseModel, Field


class Event(BaseModel):
    id: int
    title: str
    image: str
    description: str
    tags: List[str]
    location: str

    model_config = {
        "json_schema_extra": {
            "example": {
                "id": 1,
                "title": "FastAPI Book Launch",
                "image": "https://linktomymage.com/image.png",
                "description": "We will be discussing the contents of the FastAPI book in this event.",
                "tags": ["python", "fastapi", "book", "launch"],
                "location": "Google Meet"
            }
        }
    }


class EventUpdate(BaseModel):
    """Модель для обновления события — без id (id берётся из URL)."""
    title: str
    image: str
    description: str
    tags: List[str]
    location: str

    model_config = {
        "json_schema_extra": {
            "example": {
                "title": "FastAPI Book Launch (updated)",
                "image": "https://linktomymage.com/image2.png",
                "description": "Updated description.",
                "tags": ["python", "fastapi", "updated"],
                "location": "Zoom"
            }
        }
    }