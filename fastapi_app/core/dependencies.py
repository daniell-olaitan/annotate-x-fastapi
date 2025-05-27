from fastapi import Request, Depends, Path
from src.models import User, Project
from storage.repository import SQLModelUserRepsitory, SQLModelProjectRepository
from sqlmodel import Session
from typing import Annotated, AsyncGenerator
from storage.orm import engine
from fastapi.exceptions import HTTPException


async def get_db() -> AsyncGenerator[Session, None]:
    db = Session(engine)
    try:
        yield db
    finally:
        db.close()


async def load_logged_in_user(
    request: Request,
    db: Annotated[Session, Depends(get_db)]
) -> User | None:
    user_id = request.session.get('user_id')
    if user_id is None:
        return None

    user_repo = SQLModelUserRepsitory(db)

    return user_repo.get_by_id(user_id)


async def fetch_project(
    id: Annotated[str, Path()],
    db: Annotated[Session, Depends(get_db)]
) -> Project:
    project = SQLModelProjectRepository(db).get_by_id(id)
    if not project:
        raise HTTPException(status_code=404, detail='Invalid project id')

    return project


async def require_login(user: Annotated[User, Depends(load_logged_in_user)]) -> User | None:
    if user is None:
        raise HTTPException(status_code=401, detail='user is not signed in')

    return user
