from fastapi import FastAPI

from ceres.character.app import create_backend
from ceres.character.mechanism.store import SqliteCharacterBackend


def build_app(backend: SqliteCharacterBackend | None = None) -> FastAPI:
    from ceres.character.web.routes import build_web_router

    backend = create_backend() if backend is None else backend
    app = FastAPI()
    app.include_router(build_web_router(backend), prefix='/ui')
    return app


app = build_app()
