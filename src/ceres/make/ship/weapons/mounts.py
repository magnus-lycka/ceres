import math
from typing import Annotated, ClassVar, Literal

from pydantic import Field

from ceres.shared import NoteList, _Note

from ..parts import ShipPart
from .common import MountWeapon, _mounted_weapon_cost, _mounted_weapon_notes, _mounted_weapon_power


class FixedMount(ShipPart):
    tons: ClassVar[float]
    cost: ClassVar[float]
    power: ClassVar[float]
    mount_cost: ClassVar[int] = 100_000
    tl: int = 9
    pop_up: bool = False
    weapons: list[MountWeapon] = Field(default_factory=list)

    def check_tl(self) -> None:
        super().check_tl()
        if self.pop_up and self.assembly_tl < 10:
            self.error(f'Requires TL10, ship is TL{self.assembly_tl}')

    def item_description(self) -> str:
        if len(self.weapons) == 1:
            return self.weapons[0].item_description()
        return 'Fixed Mount'

    def build_notes(self) -> list[_Note]:
        notes = NoteList(super().build_notes())
        if self.pop_up:
            notes.info('Pop-up mounting: concealed until deployed')
        if len(self.weapons) == 1:
            cust = self.weapons[0].customisation_note()
            return [*notes, cust] if cust else notes
        return [*notes, *_mounted_weapon_notes(self.weapons, empty_message='No weapons in mount')]

    @property
    def tons(self) -> float:
        return 1.0 if self.pop_up else 0.0

    @property
    def cost(self) -> float:
        pop_up_cost = 1_000_000.0 if self.pop_up else 0.0
        return self.mount_cost + pop_up_cost + _mounted_weapon_cost(self.weapons)

    @property
    def power(self) -> float:
        power = _mounted_weapon_power(self.weapons)
        # Firmpoint reduces power by 25%; apply combined then floor
        power *= 0.75
        return float(math.floor(power))


TurretSize = Literal['single', 'double', 'triple', 'quad']


class _Turret(ShipPart):
    tons: ClassVar[float]
    cost: ClassVar[float]
    power: ClassVar[float]
    turret_type: str
    size: ClassVar[TurretSize]
    mount_cost: ClassVar[float]
    mount_power: ClassVar[float]
    capacity: ClassVar[int]
    pop_up: bool = False
    weapons: list[MountWeapon] = Field(default_factory=list)

    def check_tl(self) -> None:
        super().check_tl()
        if self.pop_up and self.assembly_tl < 10:
            self.error(f'Requires TL10, ship is TL{self.assembly_tl}')

    def item_description(self) -> str:
        return f'{self.size.title()} Turret'

    def build_notes(self) -> list[_Note]:
        notes = NoteList(_mounted_weapon_notes(self.weapons, empty_message='No weapons in turret'))
        if self.pop_up:
            notes.info('Pop-up mounting: concealed until deployed')
        return notes

    @property
    def group_key(self) -> str:
        note_messages = tuple(note.message for note in self._display_notes_for_grouping())
        return repr((self.build_item(), note_messages))

    def _display_notes_for_grouping(self) -> list[_Note]:
        return self.build_notes()

    def model_post_init(self, __context) -> None:
        super().model_post_init(__context)
        if len(self.weapons) > self.capacity:
            self.error(f'Turret can mount at most {self.capacity} weapon{"s" if self.capacity != 1 else ""}')

    @property
    def tons(self) -> float:
        return 2.0 if self.pop_up else 1.0

    @property
    def cost(self) -> float:
        pop_up_cost = 1_000_000.0 if self.pop_up else 0.0
        return self.mount_cost + pop_up_cost + _mounted_weapon_cost(self.weapons)

    @property
    def power(self) -> float:
        return self.mount_power + _mounted_weapon_power(self.weapons)


class SingleTurret(_Turret):
    turret_type: Literal['single_turret'] = 'single_turret'
    size: ClassVar[TurretSize] = 'single'
    tl: int = 7
    mount_cost: ClassVar[float] = 200_000.0
    mount_power: ClassVar[float] = 1.0
    capacity: ClassVar[int] = 1


class DoubleTurret(_Turret):
    turret_type: Literal['double_turret'] = 'double_turret'
    size: ClassVar[TurretSize] = 'double'
    tl: int = 8
    mount_cost: ClassVar[float] = 500_000.0
    mount_power: ClassVar[float] = 1.0
    capacity: ClassVar[int] = 2


class TripleTurret(_Turret):
    turret_type: Literal['triple_turret'] = 'triple_turret'
    size: ClassVar[TurretSize] = 'triple'
    tl: int = 9
    mount_cost: ClassVar[float] = 1_000_000.0
    mount_power: ClassVar[float] = 1.0
    capacity: ClassVar[int] = 3


class QuadTurret(_Turret):
    turret_type: Literal['quad_turret'] = 'quad_turret'
    size: ClassVar[TurretSize] = 'quad'
    tl: int = 10
    mount_cost: ClassVar[float] = 2_000_000.0
    mount_power: ClassVar[float] = 2.0
    capacity: ClassVar[int] = 4


type Turret = Annotated[
    SingleTurret | DoubleTurret | TripleTurret | QuadTurret,
    Field(discriminator='turret_type'),
]
