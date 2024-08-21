import stt
from fastapi import FastAPI, WebSocket
from fastapi.staticfiles import StaticFiles
from users.router import user_router
from chat.router import chat_router
from chat.websocket import websocket_router
from contextlib import asynccontextmanager
from database.database import init_db
from starlette.middleware.sessions import SessionMiddleware
from fastapi.middleware.cors import CORSMiddleware
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield

app = FastAPI(lifespan=lifespan)
# app = FastAPI()
app.include_router(user_router)
app.include_router(chat_router)
# app.include_router(websocket_router)


app.add_middleware(SessionMiddleware, secret_key="jl3k3aXwMhFM4jwF-kjj-Q2oIU00BxCD0kQjLeUUeqs")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)
# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")
# Mount the static files directory to serve audio files
app.mount("/audio_file", StaticFiles(directory="audio_file"), name="audio_file")
