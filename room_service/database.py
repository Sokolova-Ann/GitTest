from beanie import init_beanie
from pymongo import AsyncMongoClient
from models import Room, ChatMessage, Poll, PollOption

async def init_db():
    client = AsyncMongoClient("mongodb://localhost:27017")
    await init_beanie(
        database=client.rooms_db,
        document_models=[Room, ChatMessage, Poll, PollOption]
    )