from enum import StrEnum
from typing import Self

from pydantic import BaseModel, Field, PrivateAttr


class _NoteCategory(StrEnum):
    ITEM = 'item'
    CONTENT = 'content'
    INFO = 'info'
    WARNING = 'warning'
    ERROR = 'error'


class _Note(BaseModel):
    category: _NoteCategory
    message: str

    @classmethod
    def item(cls, message: str) -> Self:
        return cls(category=_NoteCategory.ITEM, message=message)

    @classmethod
    def content(cls, message: str) -> Self:
        return cls(category=_NoteCategory.CONTENT, message=message)

    @classmethod
    def info(cls, message: str) -> Self:
        return cls(category=_NoteCategory.INFO, message=message)

    @classmethod
    def warning(cls, message: str) -> Self:
        return cls(category=_NoteCategory.WARNING, message=message)

    @classmethod
    def error(cls, message: str) -> Self:
        return cls(category=_NoteCategory.ERROR, message=message)


def _set_item_note(notes: list[_Note], message: str) -> None:
    item_note = _Note.item(message)
    if notes and notes[0].category is _NoteCategory.ITEM:
        notes[0] = item_note
    else:
        notes.insert(0, item_note)


def _append_note(notes: list[_Note], category: _NoteCategory, message: str) -> None:
    factories = {
        _NoteCategory.CONTENT: _Note.content,
        _NoteCategory.INFO: _Note.info,
        _NoteCategory.WARNING: _Note.warning,
        _NoteCategory.ERROR: _Note.error,
    }
    if category is _NoteCategory.ITEM:
        _set_item_note(notes, message)
        return
    notes.append(factories[category](message))


class NoteList(list[_Note]):
    def _with_categories(self, *categories: _NoteCategory) -> Self:
        return type(self)(note for note in self if note.category in categories)

    def _without_categories(self, *categories: _NoteCategory) -> Self:
        return type(self)(note for note in self if note.category not in categories)

    def _messages(self, *categories: _NoteCategory) -> list[str]:
        return [note.message for note in self if note.category in categories]

    @property
    def items(self) -> list[str]:
        return self._messages(_NoteCategory.ITEM)

    @property
    def contents(self) -> list[str]:
        return self._messages(_NoteCategory.CONTENT)

    @property
    def infos(self) -> list[str]:
        return self._messages(_NoteCategory.INFO)

    @property
    def warnings(self) -> list[str]:
        return self._messages(_NoteCategory.WARNING)

    @property
    def errors(self) -> list[str]:
        return self._messages(_NoteCategory.ERROR)

    @property
    def advisories(self) -> Self:
        return self._with_categories(_NoteCategory.INFO, _NoteCategory.WARNING)

    @property
    def problems(self) -> Self:
        return self._with_categories(_NoteCategory.WARNING, _NoteCategory.ERROR)

    @property
    def details(self) -> Self:
        return self._without_categories(_NoteCategory.ITEM)

    @property
    def detail_entries(self) -> list[dict[str, str]]:
        return [{'category': note.category.value, 'message': note.message} for note in self.details]

    @property
    def item_message(self) -> str | None:
        return self.items[0] if self.items else None

    def item(self, message: str) -> Self:
        _set_item_note(self, message)
        return self

    def content(self, message: str) -> Self:
        _append_note(self, _NoteCategory.CONTENT, message)
        return self

    def info(self, message: str) -> Self:
        _append_note(self, _NoteCategory.INFO, message)
        return self

    def warning(self, message: str) -> Self:
        _append_note(self, _NoteCategory.WARNING, message)
        return self

    def error(self, message: str) -> Self:
        _append_note(self, _NoteCategory.ERROR, message)
        return self


class CeresModel(BaseModel):
    notes: list[_Note] = Field(default_factory=NoteList)

    def build_item(self) -> str | None:
        return None

    def build_notes(self) -> list[_Note]:
        return []

    def item(self, message: str) -> None:
        _set_item_note(self.notes, message)

    def info(self, message: str) -> None:
        _append_note(self.notes, _NoteCategory.INFO, message)

    def content(self, message: str) -> None:
        _append_note(self.notes, _NoteCategory.CONTENT, message)

    def error(self, message: str) -> None:
        _append_note(self.notes, _NoteCategory.ERROR, message)

    def warning(self, message: str) -> None:
        _append_note(self.notes, _NoteCategory.WARNING, message)

    def model_post_init(self, __context) -> None:
        self.notes.clear()
        if message := self.build_item():
            self.item(message)
        self.notes.extend(self.build_notes())


class Assembly(CeresModel):
    """Base for any context a part can be installed into (ship, equipment container, etc.)."""

    tl: int = 0


class CeresPart(CeresModel):
    """Base class for all parts — gear items, ship parts, etc.

    Carries the two universal part properties: technology level and unit cost.
    Context-specific properties (tons, power …) live in pure-Python mixins so
    that a single part class can appear in multiple assembly contexts without
    inheriting a second domain-model chain.
    """

    _assembly: Assembly | None = PrivateAttr(default=None)
    tl: int = 0
    cost: float = 0.0
    model_config = {'frozen': True}

    @property
    def assembly(self) -> Assembly:
        if self._assembly is None:
            raise RuntimeError(f'{type(self).__name__} not bound to an Assembly')
        return self._assembly


class Equipment(Assembly):
    parts: list[CeresPart] = Field(default_factory=list)
    cost: float = 0.0
    mass_kg: float = 0.0
    model_config = {'frozen': True}
