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
        self.notes.clear()
        if message := self.build_item():
            self.item(message)
        self.notes.extend(self.build_notes())


class CeresPart(CeresModel):
    """Base class for all parts — gear items, ship parts, etc.

    Carries the two universal part properties: technology level and unit cost.
    Context-specific properties (tons, power …) live in pure-Python mixins so
    that a single part class can appear in multiple assembly contexts without
    inheriting a second domain-model chain.
    """

    tl: int = 0
    cost: float = 0.0
    model_config = {'frozen': True}


class Equipment(CeresModel):
    parts: list[CeresPart] = Field(default_factory=list)
    tl: int = 0
    cost: float = 0.0
    mass_kg: float = 0.0
    model_config = {'frozen': True}
