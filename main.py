from fastapi import FastAPI
from routes.users import user_router
from routes.events import event_router

app = FastAPI(title="Event Planner")

app.include_router(user_router, prefix="/user")
app.include_router(event_router, prefix="/event")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8080, reload=True)