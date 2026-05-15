from math import ceil
from typing import Annotated, Any, ClassVar, Literal

from pydantic import Field

from ceres.shared import CeresModel

from .chassis import Trait


class _LocomotionBase(CeresModel):
    model_config = {'frozen': True}

    _required_tl: ClassVar[int]
    _agility: ClassVar[int | None]
    _base_endurance: ClassVar[int]
    _cost_multiplier: ClassVar[float]
    _base_speed: ClassVar[int]
    _locomotion_traits: ClassVar[tuple[Trait, ...]]
    _none_locomotion: ClassVar[bool]

    # refs/robot/08_locomotion_modifications.md — Tactical Speed Reduction
    speed_reduction: int = Field(default=0, ge=0)

    def model_post_init(self, __context: Any) -> None:
        if self.speed_reduction > self._base_speed:
            raise ValueError(f'speed_reduction {self.speed_reduction} exceeds base speed {self._base_speed}')

    @property
    def required_tl(self) -> int:
        return self._required_tl

    @property
    def agility(self) -> int | None:
        return self._agility

    @property
    def base_endurance(self) -> float:
        return self._base_endurance * (1.0 + 0.1 * self.speed_reduction)

    @property
    def cost_multiplier(self) -> float:
        return self._cost_multiplier

    @property
    def base_speed(self) -> int:
        return self._base_speed

    @property
    def effective_speed(self) -> int:
        return self._base_speed - self.speed_reduction

    @property
    def speed_cost_fraction(self) -> float:
        return -0.1 * self.speed_reduction

    @property
    def locomotion_traits(self) -> tuple[Trait, ...]:
        return self._locomotion_traits

    @property
    def is_none_locomotion(self) -> bool:
        return self._none_locomotion

    def label(self) -> str:
        raise NotImplementedError

    def speed_label(self) -> str:
        return f'{self.effective_speed}m'

    def slots_bonus(self, base_slots: int) -> int:
        if self._none_locomotion:
            return ceil(base_slots * 1.25) - base_slots
        return 0


# refs/robot/05_locomotion.md — Robot Locomotion table


class NoneLocomotion(_LocomotionBase):
    type: Literal['NONE'] = 'NONE'
    _required_tl: ClassVar[int] = 5
    _agility: ClassVar[int | None] = None
    _base_endurance: ClassVar[int] = 216
    _cost_multiplier: ClassVar[float] = 1.0
    _base_speed: ClassVar[int] = 0
    _locomotion_traits: ClassVar[tuple[Trait, ...]] = ()
    _none_locomotion: ClassVar[bool] = True

    def label(self) -> str:
        return 'None'


class WheelsLocomotion(_LocomotionBase):
    type: Literal['WHEELS'] = 'WHEELS'
    _required_tl: ClassVar[int] = 5
    _agility: ClassVar[int | None] = 0
    _base_endurance: ClassVar[int] = 72
    _cost_multiplier: ClassVar[float] = 2.0
    _base_speed: ClassVar[int] = 5
    _locomotion_traits: ClassVar[tuple[Trait, ...]] = ()
    _none_locomotion: ClassVar[bool] = False

    def label(self) -> str:
        return 'Wheels'


class WheelsAtvLocomotion(_LocomotionBase):
    type: Literal['WHEELS_ATV'] = 'WHEELS_ATV'
    _required_tl: ClassVar[int] = 5
    _agility: ClassVar[int | None] = 0
    _base_endurance: ClassVar[int] = 72
    _cost_multiplier: ClassVar[float] = 3.0
    _base_speed: ClassVar[int] = 5
    _locomotion_traits: ClassVar[tuple[Trait, ...]] = (Trait('ATV'),)
    _none_locomotion: ClassVar[bool] = False

    def label(self) -> str:
        return 'Wheels, ATV'


class TracksLocomotion(_LocomotionBase):
    type: Literal['TRACKS'] = 'TRACKS'
    _required_tl: ClassVar[int] = 5
    _agility: ClassVar[int | None] = -1
    _base_endurance: ClassVar[int] = 72
    _cost_multiplier: ClassVar[float] = 2.0
    _base_speed: ClassVar[int] = 5
    _locomotion_traits: ClassVar[tuple[Trait, ...]] = (Trait('ATV'),)
    _none_locomotion: ClassVar[bool] = False

    def label(self) -> str:
        return 'Tracks'


class GravLocomotion(_LocomotionBase):
    type: Literal['GRAV'] = 'GRAV'
    _required_tl: ClassVar[int] = 9
    _agility: ClassVar[int | None] = 1
    _base_endurance: ClassVar[int] = 24
    _cost_multiplier: ClassVar[float] = 20.0
    _base_speed: ClassVar[int] = 5
    _locomotion_traits: ClassVar[tuple[Trait, ...]] = (Trait('Flyer', 'idle'),)
    _none_locomotion: ClassVar[bool] = False

    def label(self) -> str:
        return 'Grav'


class AeroplaneLocomotion(_LocomotionBase):
    type: Literal['AEROPLANE'] = 'AEROPLANE'
    _required_tl: ClassVar[int] = 5
    _agility: ClassVar[int | None] = 1
    _base_endurance: ClassVar[int] = 12
    _cost_multiplier: ClassVar[float] = 12.0
    _base_speed: ClassVar[int] = 5
    _locomotion_traits: ClassVar[tuple[Trait, ...]] = (Trait('Flyer', 'idle'),)
    _none_locomotion: ClassVar[bool] = False

    def label(self) -> str:
        return 'Aeroplane'


class AquaticLocomotion(_LocomotionBase):
    type: Literal['AQUATIC'] = 'AQUATIC'
    _required_tl: ClassVar[int] = 6
    _agility: ClassVar[int | None] = -2
    _base_endurance: ClassVar[int] = 72
    _cost_multiplier: ClassVar[float] = 4.0
    _base_speed: ClassVar[int] = 5
    _locomotion_traits: ClassVar[tuple[Trait, ...]] = (Trait('Seafarer'),)
    _none_locomotion: ClassVar[bool] = False

    def label(self) -> str:
        return 'Aquatic'


class VtolLocomotion(_LocomotionBase):
    type: Literal['VTOL'] = 'VTOL'
    _required_tl: ClassVar[int] = 7
    _agility: ClassVar[int | None] = 0
    _base_endurance: ClassVar[int] = 24
    _cost_multiplier: ClassVar[float] = 14.0
    _base_speed: ClassVar[int] = 5
    _locomotion_traits: ClassVar[tuple[Trait, ...]] = (Trait('Flyer', 'idle'),)
    _none_locomotion: ClassVar[bool] = False

    def label(self) -> str:
        return 'VTOL'


class WalkerLocomotion(_LocomotionBase):
    type: Literal['WALKER'] = 'WALKER'
    _required_tl: ClassVar[int] = 8
    _agility: ClassVar[int | None] = 0
    _base_endurance: ClassVar[int] = 72
    _cost_multiplier: ClassVar[float] = 10.0
    _base_speed: ClassVar[int] = 5
    _locomotion_traits: ClassVar[tuple[Trait, ...]] = (Trait('ATV'),)
    _none_locomotion: ClassVar[bool] = False

    def label(self) -> str:
        return 'Walker'


class HovercraftLocomotion(_LocomotionBase):
    type: Literal['HOVERCRAFT'] = 'HOVERCRAFT'
    _required_tl: ClassVar[int] = 7
    _agility: ClassVar[int | None] = 1
    _base_endurance: ClassVar[int] = 24
    _cost_multiplier: ClassVar[float] = 10.0
    _base_speed: ClassVar[int] = 5
    _locomotion_traits: ClassVar[tuple[Trait, ...]] = (Trait('ACV'),)
    _none_locomotion: ClassVar[bool] = False

    def label(self) -> str:
        return 'Hovercraft'


class ThrusterLocomotion(_LocomotionBase):
    type: Literal['THRUSTER'] = 'THRUSTER'
    _required_tl: ClassVar[int] = 7
    _agility: ClassVar[int | None] = 1
    _base_endurance: ClassVar[int] = 2
    _cost_multiplier: ClassVar[float] = 20.0
    _base_speed: ClassVar[int] = 5
    _locomotion_traits: ClassVar[tuple[Trait, ...]] = ()
    _none_locomotion: ClassVar[bool] = False

    def label(self) -> str:
        return 'Thruster'


LocomotionUnion = Annotated[
    NoneLocomotion
    | WheelsLocomotion
    | WheelsAtvLocomotion
    | TracksLocomotion
    | GravLocomotion
    | AeroplaneLocomotion
    | AquaticLocomotion
    | VtolLocomotion
    | WalkerLocomotion
    | HovercraftLocomotion
    | ThrusterLocomotion,
    Field(discriminator='type'),
]

__all__ = [
    'LocomotionUnion',
    'NoneLocomotion',
    'WheelsLocomotion',
    'WheelsAtvLocomotion',
    'TracksLocomotion',
    'GravLocomotion',
    'AeroplaneLocomotion',
    'AquaticLocomotion',
    'VtolLocomotion',
    'WalkerLocomotion',
    'HovercraftLocomotion',
    'ThrusterLocomotion',
]
