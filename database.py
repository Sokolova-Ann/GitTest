import os
from typing import Any, List, Optional, Type
from pydantic_settings import BaseSettings
from beanie import init_beanie, Document, PydanticObjectId
from pymongo import AsyncMongoClient
from pydantic import BaseModel

from models import Todo, User

class Settings(BaseSettings):
    DATABASE_URL: str

    class Config:
        env_file = ".env"

settings = Settings()

async def init_db():
  client = AsyncMongoClient(settings.DATABASE_URL)
  await init_beanie(
        database=client.get_default_database(),
        document_models=[Todo, User]
)

class Database:
    def __init__(self, model):
        self.model = model

    async def save(self, document) -> None:
        await document.create()
        return

    async def get(self, id: PydanticObjectId) -> Any:
        doc = await self.model.get(id)
        if doc:
            return doc
        return False

    async def get_all(self) -> List[Any]:
        docs = await self.model.find_all().to_list()
        return docs

    async def update(self, id: PydanticObjectId, body: BaseModel) -> Any:
        doc_id = id
        des_body = body.model_dump(exclude_unset=True)
        update_query = {"$set": {field: value for field, value in des_body.items()}}
        doc = await self.get(doc_id)
        if not doc:
            return False
        await doc.update(update_query)
        return doc

    async def delete(self, id: PydanticObjectId) -> bool:
        doc = await self.get(id)
        if not doc:
            return False
        await doc.delete()
        return True