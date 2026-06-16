"""Character connection types: contacts, allies, rivals, enemies."""

from typing import Annotated, Literal

from pydantic import Field

from ceres.character.domain.characteristics import ConnectionKind
from ceres.shared import CeresModel


class Connection(CeresModel):
    """Base class for character connections (contacts, allies, rivals, enemies)."""

    term: int | None = None
    origin: str = ''
    name: str = ''
    note: str = ''

    @property
    def display_name(self) -> str:
        return type(self).__name__


class Contact(Connection):
    kind: Literal[ConnectionKind.CONTACT] = ConnectionKind.CONTACT

    @property
    def display_name(self) -> str:
        return 'Contact'


class Ally(Connection):
    kind: Literal[ConnectionKind.ALLY] = ConnectionKind.ALLY

    @property
    def display_name(self) -> str:
        return 'Ally'


class Rival(Connection):
    kind: Literal[ConnectionKind.RIVAL] = ConnectionKind.RIVAL

    @property
    def display_name(self) -> str:
        return 'Rival'


class Enemy(Connection):
    kind: Literal[ConnectionKind.ENEMY] = ConnectionKind.ENEMY

    @property
    def display_name(self) -> str:
        return 'Enemy'


type AnyConnection = Annotated[
    Contact | Ally | Rival | Enemy,
    Field(discriminator='kind'),
]


def make_connection(
    kind: ConnectionKind,
    term: int | None = None,
    origin: str = '',
    name: str = '',
    note: str = '',
) -> AnyConnection:
    match kind:
        case ConnectionKind.CONTACT:
            return Contact(term=term, origin=origin, name=name, note=note)
        case ConnectionKind.ALLY:
            return Ally(term=term, origin=origin, name=name, note=note)
        case ConnectionKind.RIVAL:
            return Rival(term=term, origin=origin, name=name, note=note)
        case ConnectionKind.ENEMY:
            return Enemy(term=term, origin=origin, name=name, note=note)
