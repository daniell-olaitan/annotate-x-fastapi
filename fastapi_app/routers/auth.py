import bcrypt

from typing import Annotated
from utils import ImageUtil, generate_unique_name
from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi_app import templates
from fastapi_app.core.schemas import UserSchema, OutputJSON
from sqlmodel import Session
from src.models import User, Project, Category, Image
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
img_util = ImageUtil()


@auth_router.get('/demo-signin')
async def demo_signin(
    db: Annotated[Session, Depends(get_db)],
    request: Request
) -> OutputJSON:
    if not request.session.get('user_id'):
        user_repo = SQLModelUserRepsitory(db)
        usernames = user_repo.get_usernames()
        username = generate_unique_name(usernames, 'demo')

        user = User(username=username, password='demo')
        user_id = user_repo.add(user)

        request.session['user_id'] = user_id
        request.session['demo'] = True

        project_name = generate_unique_name([], 'project').upper()
        project = Project(name=project_name)
        project_id = SQLModelProjectRepository(db).add(project, user_id)

        # Handle Categories (classes)
        categories = [
            ('class1', 'purple'),
            ('class2', 'brown'),
            ('class3', 'green'),
            ('class4', 'blue')
        ]

        for name, color in categories:
            category = Category(name=name, color=color)
            _ = SQLModelCategoryRepository(db).add(category, project_id)

        # Upload Images
        demo_images_urls = SQLModelDemoRepository(db).get_image_urls()
        images = await img_util.fetch_images(demo_images_urls)

        files = []
        image_names = []

        for img in images:
            image_name = generate_unique_name(image_names, 'image')
            image_names.append(image_name)
            files.append((
                image_name,
                img.content,
                "application/octet-stream"
            ))

        try:
            uploaded_imgs = await img_util.upload_images(files, f"FASTAPI/{project_name}")
        except Exception:
            raise HTTPException(status_code=500, detail='Network Error')

        for uploaded_img in uploaded_imgs:
            image = Image(**uploaded_img)
            _ = SQLModelImageRepository(db).add(image, project_id)

        db.commit()

    return OutputJSON(data={'id': project_id})


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
                img_util.delete_all(f"FASTAPI/{project.name}")
            except Exception:
                raise HTTPException(status_code=500, detail='Network Error')

        SQLModelUserRepsitory(db).remove(user.id)
        db.commit()

    return OutputJSON()
