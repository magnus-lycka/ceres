from pydantic import BaseModel

from ceres.shared import NoteList


class TermData(BaseModel):
    """Base class for career and pre-career term definitions."""


class Term(BaseModel):
    """Base record for a completed or in-progress term (career or pre-career)."""

    kind: str  # discriminator; concrete subclasses set to a Literal
    event: str | None = None
    mishap: str | None = None
    prison: str | None = None

    @property
    def notes(self) -> NoteList:
        result = NoteList()
        if self.event:
            result.content(self.event)
        if self.mishap:
            result.warning(self.mishap)
        if self.prison:
            result.error(self.prison)
        return result
