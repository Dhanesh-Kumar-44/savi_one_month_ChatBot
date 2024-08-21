# dependencies.py
from fastapi import Request, HTTPException, Depends
from fastapi.responses import RedirectResponse
from sqlmodel import Session, select
from users.schemas import User
from database.database import get_session

def get_current_user(request: Request, session: Session = Depends(get_session)):
    user_id = request.session.get("user_id")
    if not user_id:
        raise HTTPException(status_code=302, detail="Not authenticated", headers={"Location": "/login/"})
    query = select(User).where(User.id == user_id)
    result = session.exec(query).first()
    if not result:
        raise HTTPException(status_code=302, detail="Not authenticated", headers={"Location": "/login/"})

    return user_id
