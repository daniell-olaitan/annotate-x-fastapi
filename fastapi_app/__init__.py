from config import get_settings
from fastapi import FastAPI
from fastapi_app.routers.auth import auth_router
from starlette.middleware.sessions import SessionMiddleware

settings = get_settings()

def create_app() -> FastAPI:
    app = FastAPI()
    app.include_router(auth_router)
    app.add_middleware(SessionMiddleware, secret_key=settings.secret_key)

    return app
