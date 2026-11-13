from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from beanie import PydanticObjectId
from typing import Dict, List
import httpx
import uuid
from models import Room, ChatMessage, Poll, PollOption
from database import init_db
from pymongo.errors import DuplicateKeyError

CATALOG_URL = "http://127.0.0.1:8001"

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield

app = FastAPI(title="Room Service", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, room_id: str):
        await websocket.accept()
        if room_id not in self.active_connections:
            self.active_connections[room_id] = []
        self.active_connections[room_id].append(websocket)

    def disconnect(self, websocket: WebSocket, room_id: str):
        if room_id in self.active_connections:
            self.active_connections[room_id].remove(websocket)

    async def broadcast(self, room_id: str, message: dict):
        if room_id in self.active_connections:
            for connection in self.active_connections[room_id]:
                await connection.send_json(message)

manager = ConnectionManager()

@app.post("/rooms")
async def create_room(owner_id: str, room_code: str, film_id: str = None):
    # Проверяем подписку и фильм (как и раньше)
    async with httpx.AsyncClient() as client:
        sub_resp = await client.get(f"{CATALOG_URL}/users/{owner_id}/subscription")
        if not sub_resp.json().get("is_active"):
            raise HTTPException(status_code=403, detail="Требуется подписка")
        if film_id:
            film_resp = await client.get(f"{CATALOG_URL}/films/{film_id}")
            if film_resp.status_code != 200:
                raise HTTPException(status_code=404, detail="Фильм не найден в каталоге")

    try:
        new_room = Room(code=room_code, film_id=film_id, owner_id=owner_id)
        await new_room.create()
        return {"room_code": room_code, "room_id": str(new_room.id)}
    except DuplicateKeyError:
        raise HTTPException(status_code=400, detail="Этот код комнаты уже занят. Придумайте другой.")

@app.get("/rooms/{code}")
async def get_room(code: str):
    room = await Room.find_one(Room.code == code)
    if not room: raise HTTPException(status_code=404, detail="Комната не найдена")
    return room

@app.post("/rooms/{room_id}/history")
async def save_room_history(room_id: str, user_id: str):
    room = await Room.get(room_id)
    if room and room.film_id:
        async with httpx.AsyncClient() as client:
            await client.post(f"{CATALOG_URL}/users/{user_id}/history?film_id={room.film_id}&position={room.position_sec}")
    return {"ok": True}

# --- ГОЛОСОВАНИЕ ---
@app.post("/rooms/{room_id}/poll")
async def create_poll(room_id: str, film_ids: List[str]):
    room = await Room.get(room_id)
    if not room: raise HTTPException(404, "Комната не найдена")
    
    poll = Poll(room_id=room_id)
    await poll.create()
    
    async with httpx.AsyncClient() as client:
        for fid in film_ids:
            f_res = await client.get(f"{CATALOG_URL}/films/{fid}")
            if f_res.status_code == 200:
                title = f_res.json()["title"]
                await PollOption(poll_id=str(poll.id), film_id=fid, film_title=title).create()
    
    await manager.broadcast(room_id, {"type": "poll_created", "poll_id": str(poll.id)})
    return {"poll_id": str(poll.id)}

@app.get("/rooms/{room_id}/poll")
async def get_active_poll(room_id: str):
    poll = await Poll.find_one(Poll.room_id == room_id, Poll.status == "open")
    if not poll: return None
    options = await PollOption.find(PollOption.poll_id == str(poll.id)).to_list()
    return {"id": str(poll.id), "options": options}

@app.post("/polls/{poll_id}/vote/{option_id}")
async def vote(poll_id: str, option_id: str, room_id: str):
    option = await PollOption.get(option_id)
    if not option: raise HTTPException(404, "Вариант не найден")
    option.votes += 1
    await option.save()
    await manager.broadcast(room_id, {"type": "poll_update"})
    return {"ok": True}

@app.post("/polls/{poll_id}/finish")
async def finish_poll(poll_id: str, room_id: str):
    poll = await Poll.get(poll_id)
    poll.status = "closed"
    await poll.save()
    
    options = await PollOption.find(PollOption.poll_id == poll_id).sort(-PollOption.votes).to_list()
    if options:
        winner = options[0]
        room = await Room.get(room_id)
        room.film_id = winner.film_id
        room.status = "active"
        await room.save()
        
        await manager.broadcast(room_id, {
            "type": "poll_finished", 
            "winner_film_id": winner.film_id,
            "winner_title": winner.film_title
        })
    return {"ok": True}

# --- ЧАТ И РЕАКЦИИ ---
@app.get("/rooms/{room_id}/chat")
async def get_chat(room_id: str):
    try: r_id = PydanticObjectId(room_id)
    except: return []
    msgs = await ChatMessage.find(ChatMessage.room_id == r_id).to_list()
    return [{"user_id": m.user_id, "email": m.email, "message": m.message} for m in msgs]

@app.websocket("/rooms/{room_id}/ws")
async def websocket_endpoint(websocket: WebSocket, room_id: str, user_id: str, email: str):
    await manager.connect(websocket, room_id)
    try:
        while True:
            data = await websocket.receive_text()
            try:
                import json
                msg_data = json.loads(data)
                if msg_data.get("type") == "sync":
                    room = await Room.get(room_id)
                    if room:
                        room.is_playing = msg_data.get("is_playing")
                        room.position_sec = msg_data.get("position")
                        await room.save()
                    await manager.broadcast(room_id, msg_data)
                elif msg_data.get("type") == "reaction":
                    await manager.broadcast(room_id, msg_data)
            except:
                r_id = PydanticObjectId(room_id)
                msg = ChatMessage(room_id=r_id, user_id=user_id, email=email, message=data)
                await msg.create()
                await manager.broadcast(room_id, {"type": "chat", "user_id": user_id, "email": email, "message": data})
    except WebSocketDisconnect:
        manager.disconnect(websocket, room_id)