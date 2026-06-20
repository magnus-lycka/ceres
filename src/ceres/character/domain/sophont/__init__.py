from ceres.adapters.travellermap import TravellerMapWorld
from ceres.character.domain.sophont.humaniti import HUMANITI, VILANI, Sophont

SOPHONTS: list[Sophont] = [VILANI, HUMANITI]

SOPHONT_NAMES: list[str] = [s.name for s in SOPHONTS]


def get_sophont(name: str) -> Sophont | None:
    return next((s for s in SOPHONTS if s.name == name), None)


def available_sophont_names(world: TravellerMapWorld) -> list[str]:
    return [s.name for s in SOPHONTS if s.available_at(world)]
