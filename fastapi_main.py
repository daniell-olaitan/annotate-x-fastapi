import json
import requests
import zipfile

from io import BytesIO
from json import JSONDecodeError
from typing import Annotated
from fastapi_app import create_app, templates
from fastapi import Request, Depends, Form, File, UploadFile, Body
from sqlmodel import Session
from utils import ImageUtil, generate_unique_name
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse
from fastapi.exceptions import HTTPException
from src.models import User, Project, Category, Image, Annotation
from fastapi_app.core.schemas import OutputJSON, AnnotationSchema
from fastapi_app.core.dependencies import load_logged_in_user, get_db, fetch_project, require_login
from storage.repository import (
    SQLModelImageRepository,
    SQLModelAnnotationRepository,
    SQLModelProjectRepository,
    SQLModelCategoryRepository
)

app = create_app()
img_util = ImageUtil()


@app.get('/', response_class=HTMLResponse)
async def index(request: Request, user: Annotated[User, Depends(load_logged_in_user)]):
    if user is None:
        return RedirectResponse(request.url_for('signin'), 302)

    return templates.TemplateResponse(
        request=request,
        name='pages/project.html',
        context={'username': user.username, 'project_id': None}
    )


@app.get('/project/{id}', response_class=HTMLResponse)
async def fetch_project_id(
    user: Annotated[User, Depends(load_logged_in_user)],
    project: Annotated[Project, Depends(fetch_project)],
    request: Request
):
    if user is None:
        return RedirectResponse(request.url_for('signin'), 302)

    return templates.TemplateResponse(
        request=request,
        name='pages/project.html',
        context={
            'username': user.username,
            'project_id': project.id
        }
    )


@app.post('/projects', status_code=201)
async def create_project(
    user: Annotated[User, Depends(require_login)],
    db: Annotated[Session, Depends(get_db)],
    name: Annotated[str, Form()],
    classes: Annotated[str, Form()],
    files: Annotated[list[UploadFile], File()]
) -> OutputJSON:
    try:
        project_repo = SQLModelProjectRepository(db)
        project_name = name.upper()
        project = project_repo.get(project_name)
        if project:
            raise HTTPException(status_code=400, detail='Project name already exist')

        project = Project(name=project_name)
        project_id = project_repo.add(project, user.id)

        ## Handle Categories (classes)
        # Make category names unique
        categories = {
            k.lower(): v
            for k, v in json.loads(classes).items()
        }

        for name, color in categories.items():
            category = Category(name=name, color=color)
            _ = SQLModelCategoryRepository(db).add(category, project_id)

        # Upload Images
        if files:
            image_names = []
            images = []

            for img in files:
                image_name = generate_unique_name(image_names, 'image')
                img.filename = image_name
                image_names.append(image_name)
                images.append((
                    img.filename,
                    img.file,
                    img.content_type
                ))

            try:
                img_util.delete_all(f"FASTAPI/{project_name}")
                uploaded_imgs = await img_util.upload_images(images, f"FASTAPI/{project_name}")
            except Exception:
                raise HTTPException(status_code=500, detail='Network Error')

            for uploaded_img in uploaded_imgs:
                image = Image(**uploaded_img)
                _ = SQLModelImageRepository(db).add(image, project_id)

        db.commit()
    except (KeyError, JSONDecodeError):
        raise HTTPException(status_code=400, detail='Invalid form input')

    project = project_repo.get_by_id(project_id)

    return OutputJSON(data=project.to_dict())


@app.get('/projects/{id}', dependencies=[Depends(load_logged_in_user)])
async def read_project(
    id: str,
    db: Annotated[Session, Depends(get_db)],
) -> OutputJSON:
    project = SQLModelProjectRepository(db).get_with_relationships(id)
    if not project:
        raise HTTPException(status_code=404, detail='Project not found')

    return OutputJSON(data=project.to_dict())


@app.get('/projects')
async def read_projects(
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(load_logged_in_user)]
) -> OutputJSON:
    projects = [
        project.to_dict() for project in SQLModelProjectRepository(db).list(user.id)
    ]

    return OutputJSON(data=projects)


@app.delete('/projects/{id}')
async def delete_project(
    db: Annotated[Session, Depends(get_db)],
    project: Annotated[Project, Depends(fetch_project)]
) -> OutputJSON:
    try:
        img_util.delete_all(f"FASTAPI/{project.name}")
    except Exception:
        raise HTTPException(status_code=500, detail='Network Error')

    SQLModelProjectRepository(db).remove(project.id)
    db.commit()

    return OutputJSON()


@app.post('/projects/{id}/images/{i_id}/annotations')
async def create_annotation(
    i_id: str,
    db: Annotated[Session, Depends(get_db)],
    annotations: Annotated[list[AnnotationSchema], Body()],
    project: Annotated[Project, Depends(fetch_project)]
) -> OutputJSON:
    image_repo = SQLModelImageRepository(db)
    image = image_repo.get_by_id(i_id)
    if not image:
        raise HTTPException(status_code=404, detail='Image not found')

    image_repo.remove_image_annotations(image.id)

    ## Handle Annotations
    try:
        category_repo = SQLModelCategoryRepository(db)
        for a in annotations:
            annotation = Annotation(a.x, a.y, a.width, a.height)
            category_name = a.category.name.lower()
            category = category_repo.get(category_name)
            if category:
                category_id = category.id
            else:
                category = Category(category_name, a.category.color)
                category_id = category_repo.add(category, project.id)

            _ = SQLModelAnnotationRepository(db).add(annotation, image.id, category_id)
        db.commit()
    except KeyError:
        raise HTTPException(status_code=400, detail='Invalid user input')

    return OutputJSON()


@app.post('/projects/{id}/images', status_code=201)
async def add_project_images(
    project: Annotated[Project, Depends(fetch_project)],
    db: Annotated[Session, Depends(get_db)],
    files: Annotated[list[UploadFile], File()]
) -> OutputJSON:
    # Upload Images
    if files:
        images = []
        image_files = []
        image_names = SQLModelProjectRepository(db).get_project_image_names(project.id)

        for img in files:
            image_name = generate_unique_name(image_names, 'image')
            img.filename = image_name
            image_names.append(image_name)
            image_files.append((
                img.filename,
                img.file,
                img.content_type
            ))

        try:
            uploaded_imgs = await img_util.upload_images(image_files, f"FASTAPI/{project.name}")
        except Exception:
            raise HTTPException(status_code=500, detail='Network Error')

        for uploaded_img in uploaded_imgs:
            image = Image(**uploaded_img)
            _ = SQLModelImageRepository(db).add(image, project.id)

            img = image.to_dict()
            img['annotations'] = []
            images.append(img)

        db.commit()

    return OutputJSON(data=images)


@app.delete('/images/{id}')
async def delete_image(id: str, db: Annotated[Session, Depends(get_db)]) -> OutputJSON:
    image_repo = SQLModelImageRepository(db)
    image = image_repo.get_by_id(id)
    if not image:
        raise HTTPException(status_code=404, detail='Image not found')

    try:
        img_util.delete_image(image)
    except Exception:
        raise HTTPException(status_code=500, detail='Network Error')

    image_repo.remove(image.id)
    db.commit()

    return OutputJSON()


@app.get('/export/{id}')
async def export_project(
    id: str,
    db: Annotated[Project, Depends(get_db)]
) -> StreamingResponse:
    project = SQLModelProjectRepository(db).export_project_data(id)
    if not project:
        raise HTTPException(status_code=404, detail='Project does not exist')

    project_name = project.pop('name')
    image_urls = project.pop('image_urls')

    try:
        responses = await img_util.fetch_images(image_urls)
    except requests.RequestException:
        raise HTTPException(status_code=500, detail='Network Error')

    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', compression=zipfile.ZIP_DEFLATED) as zip_file:
        for img, response in zip(project['images'], responses):
            zip_file.writestr(f"images/{img['filename']}", response.content)

        project_str = json.dumps(project, indent=2)
        zip_file.writestr("annotations.json", project_str)

    zip_buffer.seek(0)

    return StreamingResponse(
        zip_buffer,
        media_type='application/zip',
        headers={
            'Content-Disposition': f'attachment; filename="{project_name}_annotations.zip"'
        }
    )
