from pydantic import BaseModel, EmailStr, constr
from sqlmodel import SQLModel, Field, Relationship

class UserBase(SQLModel):
    username: str
    email: EmailStr
    password: str

class User(UserBase, table=True):
    id: int = Field(default=None, primary_key=True)
    chats: list["Chat"] = Relationship(back_populates="user")

class UserCreate(BaseModel):
    username: constr(min_length=3, max_length=50)
    email: EmailStr
    password: constr(min_length=8, max_length=128)

