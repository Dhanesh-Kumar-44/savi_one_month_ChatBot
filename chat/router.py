from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, select
from openai import OpenAI
import os
from dependencies import get_current_user
from database.database import get_session
from database.milvus_db import search_similar
from chat.schemas import Chat, ChatCreate
from chat.huggin_face_modules import custom_module_chatBot, speech_recognition
from jinja2 import Environment, FileSystemLoader
from pydantic import ValidationError
from dotenv import load_dotenv

load_dotenv()

chat_router = APIRouter()

templates = Jinja2Templates(directory="templates")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Jinja2 Environment
templates_dir = "templates"
env = Environment(loader=FileSystemLoader(templates_dir))


@chat_router.get("/chat/", response_class=HTMLResponse, dependencies=[Depends(get_current_user)])
async def get_chat(request: Request, session: Session = Depends(get_session)):

    user_id = request.session.get("user_id")
    filter_chat_history = get_user_chat(user_id, session)
    return templates.TemplateResponse("chat.html", {"request": request, "chat_history": filter_chat_history})

@chat_router.post("/chat/", dependencies=[Depends(get_current_user)])
async def post_chat(request: Request, session: Session = Depends(get_session)):
    user_form = await request.form()
    module = user_form.get("module")
    user_id = request.session.get("user_id")
    user_message = user_form.get("message")
    try:
        user_create = ChatCreate(user_message=user_message, bot_message='')
    except ValidationError as e:
        return templates.TemplateResponse("chat.html", {"request": request, "user_id":user_id, "error": e.errors()})

    search_vector_data = search_similar(user_message)
    prompt = make_prompt(user_message, search_vector_data)
    print("Module Type: ",module)
    if module == "custom":
        bot_message = custom_module_chatBot(prompt)
    else:
        response = generate_response_from_chatGTP(prompt)
        bot_message = response.to_dict()['choices'][0]['message']['content']
    # save data into Chat tabel
    # Create a chat message associated with the user
    print("AI Bot Message: ",bot_message)
    new_chat = Chat(user_id=user_id, user_message=user_message, bot_message=bot_message)
    session.add(new_chat)
    session.commit()
    # session.refresh(new_chat)
    print("Chat Created")
    chat_history = get_user_chat(user_id,session)
    return templates.TemplateResponse("chat.html", {"request": request, "chat_history": chat_history, "user_id":user_id})


def get_user_chat(user_id, session):
    filter_chat_history = []
    if user_id:
        query = select(Chat).where(Chat.user_id == user_id)
        chat_result = session.exec(query)
        for chat in chat_result:
            filter_chat_history.append({"user": chat.user_message, "bot": chat.bot_message.replace("'", "\\'")})
    return filter_chat_history

def make_prompt(user_query, results):
    v_result = ""
    if results:
        for item in results[0]:
            v_result += 'brand: ' + item.entity.get("brand") + '\n'
            v_result += 'category: ' + item.entity.get("category") + '\n'
            v_result += 'description: ' + item.entity.get("description") + '\n\n\n'

    # prompt = f"Query: '''{user_query}'''\nResults from Vector Database:\n'''\n{v_result}'''\nYour task is to filter, correct, and optimize these results to ensure the highest relevance and accuracy for the query."
    prompt = f"This is my user query: '''{user_query}'''. Below is the search result from my vector database:\n'''\n{v_result}'''\nBased on this user query, please filter, correct, and optimize the search results to provide the most relevant and accurate information."
    return prompt

def generate_response_from_chatGTP(prompt):
    client = OpenAI(
    # This is the default and can be omitted
    api_key=OPENAI_API_KEY,
    )

    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
        model="gpt-3.5-turbo",
    )
    return chat_completion
