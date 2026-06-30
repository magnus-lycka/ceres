from fastapi import FastAPI

from ceres.character.service import CharacterService


def build_app(service: CharacterService | None = None) -> FastAPI:
    from ceres.character.web.routes import build_web_router

    service = CharacterService() if service is None else service
    app = FastAPI()
    app.include_router(build_web_router(service), prefix='/ui')
    return app


app = build_app()
