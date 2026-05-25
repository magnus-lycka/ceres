from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, TypeAdapter

from ceres.character.events import AnyEvent
from ceres.character.projection import CharacterProjection
from ceres.character.replay import ReplayError
from ceres.character.skills import skill_list
from ceres.character.sophonts import SOPHONTS
from ceres.character.store import CharacterRow, SqliteCharacterBackend

_event_adapter: TypeAdapter[AnyEvent] = TypeAdapter(AnyEvent)


class CharacterCreate(BaseModel):
    sophont: str
    name: str
    player: str = 'NPC'


class CharacterPatch(BaseModel):
    name: str


class SophontList(BaseModel):
    sophonts: list[str]


class SkillResponse(BaseModel):
    type: str
    specialities: list[str]


class SkillList(BaseModel):
    skills: list[SkillResponse]


class CharacterList(BaseModel):
    characters: list[CharacterRow]


class EventsResponse(BaseModel):
    events: list[dict]


def build_app(backend: SqliteCharacterBackend | None = None) -> FastAPI:
    from ceres.character.web.routes import build_web_router

    backend = SqliteCharacterBackend() if backend is None else backend
    app = FastAPI()
    app.include_router(build_web_router(backend), prefix='/ui')

    @app.get('/sophonts')
    def list_sophonts() -> SophontList:
        return SophontList(sophonts=SOPHONTS)

    @app.get('/skills')
    def list_skills() -> SkillList:
        return SkillList(
            skills=[SkillResponse(type=skill.type, specialities=list(skill.specialities)) for skill in skill_list()]
        )

    @app.post('/characters')
    def create_character(character: CharacterCreate) -> CharacterRow:
        if not character.name:
            raise HTTPException(status_code=400, detail='Name must not be empty')
        if character.sophont not in SOPHONTS:
            raise HTTPException(status_code=400, detail=f'Unknown sophont: {character.sophont}')
        return backend.start(sophont=character.sophont, player=character.player, name=character.name)

    @app.get('/characters')
    def list_characters() -> CharacterList:
        return CharacterList(characters=backend.list_characters())

    @app.get('/characters/{character_id}')
    def get_character(character_id: int) -> CharacterRow:
        character = backend.get_character(character_id)
        if character is None:
            raise HTTPException(status_code=404, detail=f'Unknown character creation id: {character_id}')
        return character

    @app.patch('/characters/{character_id}')
    def update_character(character_id: int, character: CharacterPatch) -> CharacterRow:
        if not character.name:
            raise HTTPException(status_code=400, detail='Name must not be empty')
        renamed = backend.rename_character(character_id, character.name)
        if renamed is None:
            raise HTTPException(status_code=404, detail=f'Unknown character creation id: {character_id}')
        return renamed

    @app.delete('/characters/{character_id}')
    def delete_character(character_id: int) -> CharacterRow:
        deleted = backend.delete_character(character_id)
        if deleted is None:
            raise HTTPException(status_code=404, detail=f'Unknown character creation id: {character_id}')
        return deleted

    @app.get('/characters/{character_id}/projection')
    def get_projection(character_id: int) -> CharacterProjection:
        projection = backend.get_projection(character_id)
        if projection is None:
            raise HTTPException(status_code=404, detail=f'Unknown character creation id: {character_id}')
        return projection

    @app.post('/characters/{character_id}/events')
    def post_event(character_id: int, body: dict) -> CharacterProjection:
        if backend.get_character(character_id) is None:
            raise HTTPException(status_code=404, detail=f'Unknown character creation id: {character_id}')
        try:
            event = _event_adapter.validate_python(body)
        except Exception as exc:
            raise HTTPException(status_code=400, detail=f'Invalid event: {exc}') from exc
        try:
            backend.append_event(character_id, event)
        except ReplayError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        projection = backend.get_projection(character_id)
        if projection is None:
            raise HTTPException(status_code=500, detail='Projection unavailable after event')
        return projection

    @app.get('/characters/{character_id}/events')
    def list_events(character_id: int) -> EventsResponse:
        events = backend.load_typed_events(character_id)
        if events is None:
            raise HTTPException(status_code=404, detail=f'Unknown character creation id: {character_id}')
        return EventsResponse(events=[e.model_dump() for e in events])

    return app


app = build_app()
