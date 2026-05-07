from collections.abc import Sequence
from enum import StrEnum
from typing import Annotated, ClassVar, Literal, Protocol

from pydantic import BaseModel, Field


class ResidenceDemand(StrEnum):
    PASSENGER_STATEROOM = 'Passenger Stateroom'
    PASSENGER_STATEROOM_BED = 'Passenger Stateroom Bed'
    CREW_STATEROOM = 'Crew Stateroom'
    CREW_STATEROOM_BED = 'Crew Stateroom Bed'
    ANYTHING = 'Anything'
    ANY_CREW_BED = 'Any Crew Bed'
    LOW_BERTH = 'Low Berth'


class Occupant(Protocol):
    demand: ResidenceDemand


class Residence(Protocol):
    provides: list[tuple[ResidenceDemand, int]]


class ShipOccupantBase(BaseModel):
    demand: ClassVar[ResidenceDemand]


class HighPassage(ShipOccupantBase):
    kind: Literal['high'] = 'high'
    demand: ClassVar[ResidenceDemand] = ResidenceDemand.PASSENGER_STATEROOM


class MiddlePassage(ShipOccupantBase):
    kind: Literal['middle'] = 'middle'
    demand: ClassVar[ResidenceDemand] = ResidenceDemand.PASSENGER_STATEROOM_BED


class BasicPassage(ShipOccupantBase):
    kind: Literal['basic'] = 'basic'
    demand: ClassVar[ResidenceDemand] = ResidenceDemand.ANYTHING


class LowPassage(ShipOccupantBase):
    kind: Literal['low'] = 'low'
    demand: ClassVar[ResidenceDemand] = ResidenceDemand.LOW_BERTH


class Owner(ShipOccupantBase):
    kind: Literal['owner'] = 'owner'
    demand: ClassVar[ResidenceDemand] = ResidenceDemand.PASSENGER_STATEROOM


class Guest(ShipOccupantBase):
    kind: Literal['guest'] = 'guest'
    demand: ClassVar[ResidenceDemand] = ResidenceDemand.PASSENGER_STATEROOM_BED


class Officer(ShipOccupantBase):
    kind: Literal['officer'] = 'officer'
    demand: ClassVar[ResidenceDemand] = ResidenceDemand.CREW_STATEROOM


class Crew(ShipOccupantBase):
    kind: Literal['crew'] = 'crew'
    demand: ClassVar[ResidenceDemand] = ResidenceDemand.CREW_STATEROOM_BED


class FrozenWatch(ShipOccupantBase):
    kind: Literal['frozen_watch'] = 'frozen_watch'
    demand: ClassVar[ResidenceDemand] = ResidenceDemand.LOW_BERTH


class Troop(ShipOccupantBase):
    kind: Literal['troop'] = 'troop'
    demand: ClassVar[ResidenceDemand] = ResidenceDemand.ANY_CREW_BED


type ShipOccupant = Annotated[
    HighPassage | MiddlePassage | BasicPassage | LowPassage | Owner | Guest | FrozenWatch,
    Field(discriminator='kind'),
]


class ResidenceAllocator:
    def __init__(self, residences=None):
        if residences is None:
            residences = []
        self.residences = [_ResidenceState.from_residence(residence) for residence in residences]

    def provide_one(self, occupant: Occupant):
        if occupant.demand == ResidenceDemand.ANYTHING:
            return True
        residence = self._best_residence_for(occupant.demand)
        if residence is None:
            return False
        residence.consume(occupant.demand)
        return True

    def _best_residence_for(self, demand: ResidenceDemand):
        candidates = [residence for residence in self.residences if residence.provides(demand)]
        if not candidates:
            return None
        return min(candidates, key=lambda residence: residence.preference_score(demand))

    def provide_reject(self, occupants: Sequence[Occupant]):
        provided = []
        rejected = []
        for occupant in occupants:
            if self.provide_one(occupant):
                provided.append(occupant)
            else:
                rejected.append(occupant)
        return provided, rejected


class _ResidenceState:
    def __init__(self, provides: list[tuple[ResidenceDemand, int]]):
        self.provides_list = list(provides)

    @classmethod
    def from_residence(cls, residence: Residence):
        return cls(list(residence.provides))

    def provides(self, demand: ResidenceDemand) -> bool:
        return any(provision == demand and count > 0 for provision, count in self.provides_list)

    def preference_score(self, demand: ResidenceDemand) -> tuple[int, int]:
        demand_capacity = sum(count for provision, count in self.provides_list if provision == demand)
        total_capacity = sum(count for _, count in self.provides_list)
        return demand_capacity, total_capacity

    def consume(self, demand: ResidenceDemand) -> None:
        for provision, count in self.provides_list:
            if provision != demand:
                continue
            if count > 1:
                self.provides_list = [(provision, count - 1)]
            else:
                self.provides_list = []
            return
