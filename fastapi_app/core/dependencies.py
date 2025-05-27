from fastapi import Request, Depends
from src.models import User
from storage.repository import SQLModelUserRepsitory
from sqlmodel import Session
from typing import Annotated
from storage.orm import engine


def get_db():
    db = Session(engine)
    try:
        yield db
    finally:
        db.close()


def load_logged_in_user(request: Request, db: Annotated[Session, Depends(get_db)]) -> User:
    user_id = request.session.get('user_id')
    if user_id is None:
        return None

    user_repo = SQLModelUserRepsitory(db)

    return user_repo.get_by_id(user_id)
