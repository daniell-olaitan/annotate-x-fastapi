from typing import Annotated
from fastapi_app import create_app, templates
from fastapi import Request, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, RedirectResponse
from src.models import User
from fastapi_app.core.dependencies import load_logged_in_user
from storage.repository import (
    SQLModelUserRepsitory,
    SQLModelImageRepository,
    SQLModelAnnotationRepository,
    SQLModelProjectRepository,
    SQLModelCategoryRepository,
    SQLModelDemoRepository
)

app = create_app()


@app.get('/', response_class=HTMLResponse)
async def index(request: Request, user: Annotated[User, Depends(load_logged_in_user)]):
    if user is None:
        return RedirectResponse(request.url_for('signin'), 302)

    return templates.TemplateResponse(
        request=request,
        name='pages/project.html',
        context={'username': user.username, 'project_id': None}
    )
