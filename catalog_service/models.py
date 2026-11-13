from beanie import Document
from pydantic import Field, EmailStr
from typing import Optional
from bson import ObjectId
import datetime

class Film(Document):
    id: Optional[str] = Field(default_factory=lambda: str(ObjectId()), alias="_id")
    title: str
    genre: str
    duration_sec: int
    rating: float
    poster_url: Optional[str] = None

    class Settings:
        name = "films"

class Subscription(Document):
    user_id: str
    is_active: bool = True

    class Settings:
        name = "subscriptions"

class User(Document):
    email: EmailStr
    password: str

    class Settings:
        name = "users"

class Friendship(Document):
    user_id: str        # Кто отправил заявку
    friend_id: str      # Кому отправили
    friend_email: str   # Email того, кому отправили
    status: str = "pending"  # "pending" или "accepted"

    class Settings:
        name = "friendships"

class WatchHistory(Document):
    user_id: str
    film_id: str
    film_title: str
    last_position_sec: int
    watched_at: datetime.datetime = datetime.datetime.now(datetime.UTC)

    class Settings:
        name = "watch_history"