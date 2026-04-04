from pydantic import BaseModel, Field


class Note(BaseModel):
    severity: str
    message: str


class CeresModel(BaseModel):
    notes: list[Note] = Field(default_factory=list)

    def clear_notes(self) -> None:
        object.__setattr__(self, 'notes', [])

    def error(self, message: str) -> None:
        self.notes.append(Note(severity='error', message=message))

    def warning(self, message: str) -> None:
        self.notes.append(Note(severity='warning', message=message))


class ShipBase(CeresModel):
    """Minimal ship interface that ShipPart subclasses depend on."""

    tl: int
    displacement: int

    @property
    def armour_volume_modifier(self) -> float:
        return 1.0

    def parts_of_type(self, part_cls: type) -> list:
        return []
