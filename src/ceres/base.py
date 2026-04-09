from enum import StrEnum

from pydantic import BaseModel, Field


class NoteCategory(StrEnum):
    ITEM = 'item'
    INFO = 'info'
    WARNING = 'warning'
    ERROR = 'error'


class Note(BaseModel):
    category: NoteCategory
    message: str


class CeresModel(BaseModel):
    notes: list[Note] = Field(default_factory=list)

    def build_item(self) -> str | None:
        return None

    def build_notes(self) -> list[Note]:
        return []

    def item(self, message: str) -> None:
        item_note = Note(category=NoteCategory.ITEM, message=message)
        if self.notes and self.notes[0].category is NoteCategory.ITEM:
            self.notes[0] = item_note
            return
        self.notes.insert(0, item_note)

    def info(self, message: str) -> None:
        self.notes.append(Note(category=NoteCategory.INFO, message=message))

    def error(self, message: str) -> None:
        self.notes.append(Note(category=NoteCategory.ERROR, message=message))

    def warning(self, message: str) -> None:
        self.notes.append(Note(category=NoteCategory.WARNING, message=message))

    def model_post_init(self, __context) -> None:
        if message := self.build_item():
            self.item(message)
        self.notes.extend(self.build_notes())


class ShipBase(CeresModel):
    """Minimal ship interface that ShipPart subclasses depend on."""

    tl: int
    displacement: int

    @property
    def armour_volume_modifier(self) -> float:
        return 1.0

    def parts_of_type(self, part_cls: type) -> list:
        return []

    def cargo_space_for(self, hold) -> float:
        return 0.0
