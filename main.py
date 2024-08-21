from fastapi import FastAPI
from users.router import user_router
from chat.router import chat_router
from contextlib import asynccontextmanager
from database.database import init_db
from starlette.middleware.sessions import SessionMiddleware
from fastapi.middleware.cors import CORSMiddleware
import logging
from dotenv import load_dotenv
import os

# Configure logging
logging.basicConfig(level=logging.DEBUG)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield

# Load environment variables from the .env file
load_dotenv()

app = FastAPI(lifespan=lifespan)
# app = FastAPI()
app.include_router(user_router)
app.include_router(chat_router)
# app.include_router(websocket_router)

app.add_middleware(SessionMiddleware, secret_key=os.getenv("SESSION_SECRET_KEY"))
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

