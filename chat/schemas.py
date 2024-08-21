from pydantic import constr
from sqlmodel import SQLModel, Field, Relationship
from users.schemas import User

class ChatBase(SQLModel):
    user_message: str
    bot_message: str

class Chat(ChatBase, table=True):
    id: int = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    user: User = Relationship(back_populates="chats")


class ChatCreate(ChatBase):
    user_message: constr(min_length=10, max_length=50)