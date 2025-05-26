from typing import Annotated
from fastapi_app import create_app
from fastapi import Request, Depends
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, RedirectResponse
from src.models import User
from fastapi_app.core.dependencies import load_logged_in_user


app = create_app()
app.mount('/static', StaticFiles(directory='frontend/static'), name='static')
templates = Jinja2Templates(directory='frontend/templates')


@app.get('/', response_class=HTMLResponse)
async def home(request: Request, user: Annotated[User, Depends(load_logged_in_user)]):
    if user is None:
        return RedirectResponse(url_for)

    return templates.TemplateResponse(
        request=request,
        name='pages/project.html',
        context={'username': '', 'project_id': ''}
    )
