"""What a vehicle design projects for rendering.

The spec carries values, not presentation: Structure is an integer and Cost a
number. Composing the strings a stat block prints — 'High (Medium)', '6 (18)',
'Cr155000' — belongs to the report context, which is where ships put it too.

Fields arrive as the design learns to compute them. A row the model cannot yet
produce is absent rather than present and empty.
"""

from pydantic import BaseModel, Field

from ceres.shared import NoteList

from .armour import Face
from .size import VehicleSize
from .speed import SpeedBand
from .types import VehicleType


class VehicleSpec(BaseModel):
    """A design's figures, ready to render."""

    name: str
    description: str = ''

    vehicle_type: VehicleType
    size: VehicleSize
    spaces: int
    target_size_dm: int
    features_and_traits: list[str] = Field(default_factory=list)

    tl: int
    skill: str
    agility: int
    speed: SpeedBand
    cruise_speed: SpeedBand
    range_km: int | None = None
    cruise_range_km: int | None = None
    structure: int
    shipping_tons: float
    cost: float
    armour: dict[Face, int] = Field(default_factory=dict)

    notes: NoteList = Field(default_factory=NoteList)
