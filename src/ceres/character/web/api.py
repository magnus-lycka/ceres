"""JSON boundary for the shared Ceres frontend."""

from fastapi import APIRouter, HTTPException, Response
from pydantic import BaseModel, Field

from ceres.character.mechanism.errors import ReplayError
from ceres.character.presentation import CharacterView
from ceres.character.service import CharacterListItem, CharacterService


class ChoiceValues(dict[str, str]):
    """String mapping with repeated selections preserved for pending contracts."""

    def __init__(self, values: dict[str, str | list[str]]):
        self.values_by_name = values
        super().__init__(
            (key, value[0] if isinstance(value, list) and value else value if isinstance(value, str) else '')
            for key, value in values.items()
        )

    def getlist(self, key: str) -> list[str]:
        value = self.values_by_name.get(key, [])
        return value if isinstance(value, list) else [value]


class Choice(BaseModel):
    fulfills: str
    values: dict[str, str | list[str]]


class CreateCharacter(BaseModel):
    name: str = Field(min_length=1)
    player: str = 'NPC'


def build_api_router(service: CharacterService) -> APIRouter:
    router = APIRouter()

    @router.get('/characters')
    def characters() -> list[CharacterListItem]:
        return service.list_characters()

    @router.post('/characters', status_code=201)
    def create(body: CreateCharacter) -> CharacterView:
        return service.view(service.create_character(body.name, body.player))

    @router.get('/characters/{character_id}')
    def character(character_id: int) -> CharacterView:
        try:
            return service.view(character_id)
        except ReplayError as exc:
            raise HTTPException(
                409, 'This saved character cannot be replayed with the current character rules.'
            ) from exc
        except ValueError as exc:
            raise HTTPException(404, 'Source character deleted') from exc

    @router.post('/characters/{character_id}/choices')
    def choose(character_id: int, body: Choice) -> CharacterView:
        current = character(character_id)
        if current.pending is None or body.fulfills != current.pending.id:
            raise HTTPException(409, 'This choice has changed. Reload the character before continuing.')
        form = ChoiceValues(body.values)
        try:
            return service.choose(character_id, body.fulfills, form)
        except (ValueError, ReplayError) as exc:
            raise HTTPException(422, str(exc)) from exc

    @router.post('/characters/{character_id}/undo')
    def undo(character_id: int) -> CharacterView:
        character(character_id)
        try:
            return service.undo(character_id)
        except ValueError as exc:
            raise HTTPException(409, str(exc)) from exc

    @router.delete('/characters/{character_id}', status_code=204)
    def delete(character_id: int) -> Response:
        if not any(item.id == character_id for item in service.list_characters()):
            raise HTTPException(404, 'Source character deleted')
        service.delete_character(character_id)
        return Response(status_code=204)

    @router.get('/characters/{character_id}/pdf')
    def pdf(character_id: int) -> Response:
        character(character_id)
        return Response(
            service.pdf(character_id),
            media_type='application/pdf',
            headers={'Content-Disposition': 'attachment; filename="character.pdf"'},
        )

    return router
