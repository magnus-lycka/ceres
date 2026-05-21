from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from ceres.character.skills import skill_list
from ceres.character.sophonts import SOPHONTS
from ceres.character.store import CharacterEvent, CharacterRow, SqliteCharacterBackend


class CharacterCreate(BaseModel):
    sophont: str
    name: str
    player: str = 'NPC'


class CharacterPatch(BaseModel):
    name: str


class UcpPatch(BaseModel):
    changes: list[str]
    note: str | None = None


class SophontList(BaseModel):
    sophonts: list[str]


class SkillResponse(BaseModel):
    type: str
    name: str
    specialities: list[str]


class SkillList(BaseModel):
    skills: list[SkillResponse]


class CharacterList(BaseModel):
    characters: list[CharacterRow]


class CharacterDetail(BaseModel):
    id: int
    sophont: str
    player: str
    name: str
    ucp: dict[str, int]


class UcpResponse(BaseModel):
    ucp: dict[str, int]


class EventsResponse(BaseModel):
    events: list[CharacterEvent]


def build_app(backend: SqliteCharacterBackend | None = None) -> FastAPI:
    backend = SqliteCharacterBackend() if backend is None else backend
    app = FastAPI()

    @app.get('/sophonts')
    def list_sophonts() -> SophontList:
        return SophontList(sophonts=SOPHONTS)

    @app.get('/skills')
    def list_skills() -> SkillList:
        return SkillList(
            skills=[
                SkillResponse(type=skill.type, name=skill.name, specialities=list(skill.specialities))
                for skill in skill_list()
            ]
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
    def get_character(character_id: int) -> CharacterDetail:
        character = backend.get_character(character_id)
        if character is None:
            raise HTTPException(status_code=404, detail=f'Unknown character creation id: {character_id}')
        ucp = backend.get_ucp(character_id)
        return CharacterDetail(
            id=character['id'],
            sophont=character['sophont'],
            player=character['player'],
            name=character['name'],
            ucp={} if ucp is None else ucp,
        )

    @app.get('/characters/{character_id}/ucp')
    def get_ucp(character_id: int) -> UcpResponse:
        ucp = backend.get_ucp(character_id)
        if ucp is None:
            raise HTTPException(status_code=404, detail=f'Unknown character creation id: {character_id}')
        return UcpResponse(ucp=ucp)

    @app.patch('/characters/{character_id}/ucp')
    def update_ucp(character_id: int, patch: UcpPatch) -> UcpResponse:
        try:
            ucp = backend.patch_ucp(character_id, patch.changes, note=patch.note)
        except ValueError as error:
            raise HTTPException(status_code=400, detail=str(error)) from error
        if ucp is None:
            raise HTTPException(status_code=404, detail=f'Unknown character creation id: {character_id}')
        return UcpResponse(ucp=ucp)

    @app.get('/characters/{character_id}/events')
    def list_events(character_id: int) -> EventsResponse:
        events = backend.list_events(character_id)
        if events is None:
            raise HTTPException(status_code=404, detail=f'Unknown character creation id: {character_id}')
        return EventsResponse(events=events)

    @app.patch('/characters/{character_id}')
    def update_character(character_id: int, character: CharacterPatch) -> CharacterRow:
        if not character.name:
            raise HTTPException(status_code=400, detail='Name must not be empty')
        renamed = backend.rename_character(character_id, character.name)
        if renamed is None:
            raise HTTPException(status_code=404, detail=f'Unknown character creation id: {character_id}')
        return renamed

    return app


app = build_app()
