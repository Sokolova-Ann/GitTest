from beanie import init_beanie
from pymongo import AsyncMongoClient
from models import Film, Subscription, User, Friendship, WatchHistory

async def init_db():
    client = AsyncMongoClient("mongodb://localhost:27017")
    await init_beanie(
        database=client.catalog_db,
        document_models=[Film, Subscription, User, Friendship, WatchHistory]
    )