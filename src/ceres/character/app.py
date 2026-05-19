from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from ceres.character.sophonts import SOPHONTS
from ceres.character.store import CharacterRow, SqliteCharacterBackend


class CharacterCreate(BaseModel):
    sophont: str
    name: str
    player: str = 'NPC'


class CharacterPatch(BaseModel):
    name: str


class SophontList(BaseModel):
    sophonts: list[str]


class CharacterList(BaseModel):
    characters: list[CharacterRow]


def build_app(backend: SqliteCharacterBackend | None = None) -> FastAPI:
    backend = SqliteCharacterBackend() if backend is None else backend
    app = FastAPI()

    @app.get('/sophonts')
    def list_sophonts() -> SophontList:
        return SophontList(sophonts=SOPHONTS)

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
