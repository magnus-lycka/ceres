"""Character connection types: contacts, allies, rivals, enemies."""

from typing import Annotated, Literal

from pydantic import Field

from ceres.character.domain.characteristics import ConnectionKind
from ceres.shared import CeresModel


class Connection(CeresModel):
    """Base class for character connections (contacts, allies, rivals, enemies)."""

    source: str = ''
    power: int | None = None
    affinity: int | None = None
    enmity: int | None = None

    @property
    def display_name(self) -> str:
        return type(self).__name__

    @property
    def color_class(self) -> str:
        return 'text-gray-400'


class Contact(Connection):
    kind: Literal[ConnectionKind.CONTACT] = ConnectionKind.CONTACT

    @property
    def display_name(self) -> str:
        return 'Contact'

    @property
    def color_class(self) -> str:
        return 'text-cyan-400'


class Ally(Connection):
    kind: Literal[ConnectionKind.ALLY] = ConnectionKind.ALLY

    @property
    def display_name(self) -> str:
        return 'Ally'

    @property
    def color_class(self) -> str:
        return 'text-green-400'


class Rival(Connection):
    kind: Literal[ConnectionKind.RIVAL] = ConnectionKind.RIVAL

    @property
    def display_name(self) -> str:
        return 'Rival'

    @property
    def color_class(self) -> str:
        return 'text-yellow-400'


class Enemy(Connection):
    kind: Literal[ConnectionKind.ENEMY] = ConnectionKind.ENEMY

    @property
    def display_name(self) -> str:
        return 'Enemy'

    @property
    def color_class(self) -> str:
        return 'text-red-400'


type AnyConnection = Annotated[
    Contact | Ally | Rival | Enemy,
    Field(discriminator='kind'),
]


def _affinity_enmity_value(roll: int, *, enmity: bool = False) -> int:
    if roll <= 2:
        value = 0
    elif roll <= 4:
        value = 1
    elif roll <= 6:
        value = 2
    elif roll <= 8:
        value = 3
    elif roll <= 10:
        value = 4
    elif roll == 11:
        value = 5
    else:
        value = 6
    return -value if enmity else value


def _connection_affinity_enmity(
    kind: ConnectionKind,
    affinity_roll: int | None,
    enmity_roll: int | None,
) -> tuple[int | None, int | None]:
    if affinity_roll is None and enmity_roll is None:
        return None, None

    match kind:
        case ConnectionKind.ALLY:
            affinity = _affinity_enmity_value(affinity_roll) if affinity_roll is not None else None
            return affinity, 0
        case ConnectionKind.CONTACT:
            affinity = _affinity_enmity_value(affinity_roll) if affinity_roll is not None else None
            enmity = _affinity_enmity_value(enmity_roll, enmity=True) if enmity_roll is not None else None
            return affinity, enmity
        case ConnectionKind.RIVAL:
            affinity = _affinity_enmity_value(affinity_roll) if affinity_roll is not None else None
            enmity = _affinity_enmity_value(enmity_roll, enmity=True) if enmity_roll is not None else None
            return affinity, enmity
        case ConnectionKind.ENEMY:
            enmity = _affinity_enmity_value(enmity_roll, enmity=True) if enmity_roll is not None else None
            return 0, enmity


def make_connection(
    kind: ConnectionKind,
    source: str = '',
    power: int | None = None,
    affinity_roll: int | None = None,
    enmity_roll: int | None = None,
) -> AnyConnection:
    affinity, enmity = _connection_affinity_enmity(kind, affinity_roll, enmity_roll)
    match kind:
        case ConnectionKind.CONTACT:
            return Contact(source=source, power=power, affinity=affinity, enmity=enmity)
        case ConnectionKind.ALLY:
            return Ally(source=source, power=power, affinity=affinity, enmity=enmity)
        case ConnectionKind.RIVAL:
            return Rival(source=source, power=power, affinity=affinity, enmity=enmity)
        case ConnectionKind.ENEMY:
            return Enemy(source=source, power=power, affinity=affinity, enmity=enmity)
