from typing import Optional, List
from beanie import Document, PydanticObjectId
from pydantic import Field
import datetime

class Room(Document):
    id: Optional[str] = Field(default_factory=lambda: str(PydanticObjectId()), alias="_id")
    code: str = Field(unique=True) # <--- Теперь код уникальный!
    film_id: Optional[str] = None 
    owner_id: str
    status: str = "waiting"
    created_at: datetime.datetime = datetime.datetime.now(datetime.UTC)
    
    is_playing: bool = False
    position_sec: int = 0

    class Settings:
        name = "rooms"

class ChatMessage(Document):
    room_id: PydanticObjectId
    user_id: str
    email: str
    message: str
    created_at: datetime.datetime = datetime.datetime.now(datetime.UTC)

    class Settings:
        name = "messages"

class PollOption(Document):
    poll_id: str
    film_id: str
    film_title: str
    votes: int = 0

    class Settings:
        name = "poll_options"

class Poll(Document):
    id: Optional[str] = Field(default_factory=lambda: str(PydanticObjectId()), alias="_id")
    room_id: str
    status: str = "open" # open, closed
    
    class Settings:
        name = "polls"