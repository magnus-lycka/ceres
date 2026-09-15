from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse

from ceres.character.service import CharacterService
from ceres.character.web.api import build_api_router
from ceres.character.web.world_api import router as world_router


def build_app(service: CharacterService | None = None, *, web_directory: Path | None = None) -> FastAPI:
    from ceres.character.web.routes import build_web_router

    service = CharacterService() if service is None else service
    app = FastAPI()
    app.include_router(build_web_router(service), prefix='/ui')
    app.include_router(build_api_router(service), prefix='/api')
    app.include_router(world_router, prefix='/api')
    directory = (web_directory or Path(__file__).resolve().parents[4] / 'web' / 'build').resolve()

    @app.get('/{path:path}', include_in_schema=False)
    def frontend(path: str) -> FileResponse:
        if path == 'api' or path.startswith('api/'):
            raise HTTPException(404)
        candidate = (directory / path).resolve()
        if not candidate.is_relative_to(directory):
            raise HTTPException(404)
        if candidate.is_file():
            return FileResponse(candidate)
        if (candidate / 'index.html').is_file():
            return FileResponse(candidate / 'index.html')
        if Path(path).suffix or path.startswith('_app/'):
            raise HTTPException(404)
        fallback = directory / '200.html'
        if not fallback.is_file():
            raise HTTPException(503, 'Build the web interface with npm --prefix web run build.')
        return FileResponse(fallback)

    return app


app = build_app()
