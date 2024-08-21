from fastapi import APIRouter, Depends, status, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.security import OAuth2PasswordBearer
from sqlmodel import Session, select
from users.schemas import User, UserCreate
from database.database import get_session
from passlib.context import CryptContext
from dependencies import get_current_user
from chat.schemas import Chat
from pydantic import ValidationError


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth_2_scheme = OAuth2PasswordBearer(tokenUrl="token")

user_router = APIRouter()

templates = Jinja2Templates(directory="templates")


@user_router.get("/", response_class=HTMLResponse, dependencies=[Depends(get_current_user)])
async def home(request: Request, session: Session = Depends(get_session)):
    user_id = request.session.get("user_id")
    filter_chat_history = []
    if user_id:
        query = select(Chat).where(Chat.user_id == user_id)
        chat_result = session.exec(query)
        for chat in chat_result:
            filter_chat_history.append({"user": chat.user_message, "bot": chat.bot_message.replace("'", "\\'")})
    return templates.TemplateResponse("chat.html", {"request": request, "chat_history": filter_chat_history})


@user_router.get("/register/", response_class=HTMLResponse)
async def get_register(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})


@user_router.post("/register/", response_class=HTMLResponse)
async def register(request: Request, session: Session = Depends(get_session)):
    form_data = await request.form()
    try:
        user_create = UserCreate(**form_data)
    except ValidationError as e:
        return templates.TemplateResponse("register.html", {"request": request, "error": e.errors()})
    query = select(User).where(User.email == user_create.email)
    result = session.exec(query).first()
    if result:
        return templates.TemplateResponse("register.html", {"request": request, "error": "Email is already registered"})

    hashed_password = pwd_context.hash(user_create.password)
    new_user = User(username=user_create.username, email=user_create.email, password=hashed_password)
    session.add(new_user)
    session.commit()
    session.refresh(new_user)

    return templates.TemplateResponse("login.html", {"request": request, "data": new_user})

@user_router.get("/login/", response_class=HTMLResponse)
async def get_login(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@user_router.post("/login/")
async def post_login(request: Request, session: Session = Depends(get_session)):
    form_data = await request.form()
    user_query = select(User).where(User.email == form_data.get('email'))
    user = session.execute(user_query).first()
    if user and pwd_context.verify(form_data.get('password'), user.User.password):
        request.session["user_id"] = user.User.id
        return RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
    return templates.TemplateResponse("login.html", {"request": request, "error": "Invalid Credentials"})



