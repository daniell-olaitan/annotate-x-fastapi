import bcrypt

from typing import Annotated
from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi_app import templates
from fastapi_app.core.schemas import UserSchema, OutputJSON
from sqlmodel import Session
from src.models import User
from fastapi.exceptions import HTTPException
from fastapi_app.core.dependencies import load_logged_in_user, get_db
from storage.repository import (
    SQLModelUserRepsitory,
    SQLModelImageRepository,
    SQLModelAnnotationRepository,
    SQLModelProjectRepository,
    SQLModelCategoryRepository,
    SQLModelDemoRepository
)

auth_router = APIRouter()


@auth_router.get('/signin', response_class=HTMLResponse, name='signin')
async def signin(request: Request, user: Annotated[User, Depends(load_logged_in_user)]):
    if user:
        return RedirectResponse(request.url_for('index'), 302)

    return templates.TemplateResponse(
        request=request,
        name='pages/signin.html'
    )


@auth_router.post('/signin', response_class=HTMLResponse)
async def post_signin(
    request: Request,
    user_schema: UserSchema,
    user: Annotated[User, Depends(load_logged_in_user)],
    db: Annotated[Session, Depends(get_db)]
):
    if user:
        return RedirectResponse(request.url_for('index'), 302)

    user_repo = SQLModelUserRepsitory(db)
    user = user_repo.get(user_schema.username)
    if user:
        if bcrypt.checkpw(user_schema.password.encode('utf-8'), user.password.encode('utf-8')):
            request.session['user_id'] = user.id

            return RedirectResponse(request.url_for('index'), 302)
        raise HTTPException(status_code=400, detail='Invalid password')

    raise HTTPException(status_code=404, detail='User does not exist')


@auth_router.get('/signup', response_class=HTMLResponse)
async def signup(request: Request, user: Annotated[User, Depends(load_logged_in_user)]):
    if user:
        return RedirectResponse(request.url_for('index'), 302)

    return templates.TemplateResponse(
        request=request,
        name='pages/signup.html'
    )


@auth_router.post('/signup', response_class=HTMLResponse)
async def post_signup(
    request: Request,
    user_schema: UserSchema,
    user: Annotated[User, Depends(load_logged_in_user)],
    db: Annotated[Session, Depends(get_db)]
):
    if user:
        return RedirectResponse(request.url_for('index'), 302)

    user_repo = SQLModelUserRepsitory(db)
    user = user_repo.get(user_schema.username)
    if user:
        raise HTTPException(status_code=400, detail='User already exist')

    user = User(**user_schema.model_dump())
    _ = user_repo.add(user)

    db.commit()

    return RedirectResponse(request.url_for('signin'), 302)


@auth_router.get('/signout')
async def signout(
    request: Request,
    user: Annotated[User, Depends(load_logged_in_user)],
    db: Annotated[Session, Depends(get_db)]
) -> OutputJSON:
    _ = request.session.pop('user_id', None)
    demo = request.session.pop('demo', None)
    if demo:
        for project in SQLModelProjectRepository(db).list(user.id):
            try:
                pass
                # img_util.delete_all(project.name)
            except Exception:
                raise HTTPException(status_code=500, detail='Network Error')

        SQLModelUserRepsitory(db).remove(user.id)
        db.commit()

    return OutputJSON()
