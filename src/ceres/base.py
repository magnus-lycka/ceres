from pydantic import BaseModel


class ShipBase(BaseModel):
    """Minimal ship interface that ShipPart subclasses depend on."""

    tl: int
    displacement: int

    @property
    def armour_volume_modifier(self) -> float:
        return 1.0
