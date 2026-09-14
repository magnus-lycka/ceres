"""Weapon mounts: where a vehicle carries its weapons.

A mount is installed whether or not anything is mounted on it. The ATV's turret,
for instance, is published empty.

Only the mounts the current designs need are described.

Rules: refs/vehicle/17_weapons.md
"""

from math import ceil
from typing import Annotated, Literal

from pydantic import Field

from .armour import Face
from .base import InstalledInVehicle

# refs/vehicle/17_weapons.md — Turret
_TURRET_WEAPON_SPACES_PER_SPACE = 4
_TURRET_COST_PER_SPACE = 20_000


class _Mount(InstalledInVehicle):
    """What every mount can be asked, whether or not it answers."""

    @property
    def name(self) -> str:
        raise NotImplementedError

    @property
    def spaces(self) -> int:
        return 0

    @property
    def cost(self) -> float:
        return 0.0


class Turret(_Mount):
    """An armoured rotating mount, firing in every direction but through the face
    opposite the one it sits on."""

    kind: Literal['TURRET'] = 'TURRET'
    face: Face
    weapon_spaces: int
    gunners: int = 0

    @property
    def name(self) -> str:
        return 'Turret'

    @property
    def spaces(self) -> int:
        """A Space for every four Spaces of weapons it can hold, and one per gunner."""
        return ceil(self.weapon_spaces / _TURRET_WEAPON_SPACES_PER_SPACE) + self.gunners

    @property
    def cost(self) -> float:
        return _TURRET_COST_PER_SPACE * self.spaces


MountUnion = Annotated[Turret, Field(discriminator='kind')]
