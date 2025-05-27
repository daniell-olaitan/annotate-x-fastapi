from config import get_settings
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from storage.orm import SQLModel, engine
from fastapi_app.core.exception_handlers import handle_validation_exception, handle_httpexception
from fastapi.exceptions import HTTPException, RequestValidationError

settings = get_settings()
templates = Jinja2Templates(directory='fastapi_app/frontend/templates')


def create_app() -> FastAPI:
    app = FastAPI()

    from fastapi_app.routers.auth import auth_router
    app.include_router(auth_router)
    app.mount('/static', StaticFiles(directory='fastapi_app/frontend/static'), name='static')
    app.add_exception_handler(HTTPException, handle_httpexception)
    app.add_exception_handler(RequestValidationError, handle_validation_exception)
    app.add_middleware(SessionMiddleware, secret_key=settings.secret_key)

    SQLModel.metadata.create_all(engine)

    return app
