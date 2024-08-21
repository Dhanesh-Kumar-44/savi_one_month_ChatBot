from fastapi import APIRouter, Depends, status, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, select
from openai import OpenAI
import shutil
import os
from dependencies import get_current_user
from database.database import get_session
from database.milvus_db import collection_milvus, search_similar
from chat.schemas import Chat, ChatCreate
from chat.huggin_face_modules import custom_module_chatBot, speech_recognition
from jinja2 import Environment, FileSystemLoader
from pydantic import ValidationError

chat_router = APIRouter()

templates = Jinja2Templates(directory="templates")
OPENAI_API_KEY = 'provide openAI key here'

# Jinja2 Environment
templates_dir = "templates"
env = Environment(loader=FileSystemLoader(templates_dir))


# Custom filter for escaping JavaScript
# def escapejs(value):
#     return value.replace("\'", '').replace("'", "").replace('\\', '\\\\').replace('\n', '\\n').replace('\r', '\\r').replace('"', '\\"').replace("'", "\\'")
#
# env.filters['escapejs'] = escapejs


@chat_router.get("/chat/", response_class=HTMLResponse, dependencies=[Depends(get_current_user)])
async def get_chat(request: Request, session: Session = Depends(get_session)):

    user_id = request.session.get("user_id")
    filter_chat_history = get_user_chat(user_id, session)
    # template = env.get_template("chat.html")
    # return template.render({"request": request, "chat_history": filter_chat_history, "user_id":user_id})
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

    if user_form.get("voice"):
        voice_file = user_form.get("voice")
        file_location = os.path.join("/home/dhanesh/savi_month_one/ChatBot/audio_file/", voice_file.filename)
        with open(file_location, "wb") as buffer:
            shutil.copyfileobj(user_form.get("voice").file, buffer)
            user_query = speech_recognition(file_location)
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
    print("\n\n\n\n\n")
    print("chat history: ",chat_history)
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



# @chat_router.get("/get-audio/{text}")
# async def get_audio(text: str, request: Request,):
#     user_id = request.session.get("user_id")
#     audio_name = str(user_id)+"_"+text.replace(" ","")[:10]+".wav"
#     audio_url = text_to_audio(text,audio_name)
#     if audio_url:
#         # return JSONResponse(content={"audio_url": audio_url})
#         return {"audio_url": audio_url}
#     else:
#         raise HTTPException(status_code=404, detail="Audio not found")