from typing import ClassVar, Literal

from ceres.shared import NoteList, _Note

from .common import _ZeroPowerSystemPart


class _ReEntrySystem(_ZeroPowerSystemPart):
    _capacity: ClassVar[int]
    _protection: ClassVar[int | None] = None
    _detection_dm: ClassVar[int | None] = None
    _attack_dm: ClassVar[int | None] = None

    @property
    def capacity(self) -> int:
        return self._capacity

    @property
    def protection(self) -> int | None:
        return self._protection

    @property
    def detection_dm(self) -> int | None:
        return self._detection_dm

    @property
    def attack_dm(self) -> int | None:
        return self._attack_dm

    def build_notes(self) -> list[_Note]:
        notes = NoteList()
        capacity_text = 'one person' if self.capacity == 1 else 'two people'
        notes.info(f'Emergency escape and planetary insertion system for {capacity_text}')
        if self.protection is not None:
            notes.info(f'Protection +{self.protection}')
        if self.detection_dm is not None:
            notes.info(f'DM{self.detection_dm} to detect')
        if self.attack_dm is not None:
            notes.info(f'DM{self.attack_dm} against attacks')
        return notes


class BasicReEntryCapsule(_ReEntrySystem):
    system_type: Literal['BASIC_RE_ENTRY_CAPSULE'] = 'BASIC_RE_ENTRY_CAPSULE'
    tl: int = 8
    description: Literal['Re-entry Capsule (basic)'] = 'Re-entry Capsule (basic)'
    tons: ClassVar[float]
    cost: ClassVar[float]
    _capacity: ClassVar[int] = 1

    @property
    def tons(self) -> float:
        return 0.5

    @property
    def cost(self) -> float:
        return 20_000.0


class AssaultReEntryCapsule(_ReEntrySystem):
    system_type: Literal['ASSAULT_RE_ENTRY_CAPSULE'] = 'ASSAULT_RE_ENTRY_CAPSULE'
    tl: int = 10
    description: Literal['Re-entry Capsule (assault)'] = 'Re-entry Capsule (assault)'
    tons: ClassVar[float]
    cost: ClassVar[float]
    _capacity: ClassVar[int] = 1
    _protection: ClassVar[int | None] = 20
    _detection_dm: ClassVar[int | None] = -2

    @property
    def tons(self) -> float:
        return 0.5

    @property
    def cost(self) -> float:
        return 50_000.0


class HighSurvivabilityReEntryCapsule(_ReEntrySystem):
    system_type: Literal['HIGH_SURVIVABILITY_RE_ENTRY_CAPSULE'] = 'HIGH_SURVIVABILITY_RE_ENTRY_CAPSULE'
    tl: int = 14
    description: Literal['Re-entry Capsule (high-survivability)'] = 'Re-entry Capsule (high-survivability)'
    tons: ClassVar[float]
    cost: ClassVar[float]
    _capacity: ClassVar[int] = 1
    _protection: ClassVar[int | None] = 30
    _detection_dm: ClassVar[int | None] = -4
    _attack_dm: ClassVar[int | None] = -2

    @property
    def tons(self) -> float:
        return 0.5

    @property
    def cost(self) -> float:
        return 100_000.0


class ReEntryPod(_ReEntrySystem):
    system_type: Literal['RE_ENTRY_POD'] = 'RE_ENTRY_POD'
    tl: int = 9
    description: Literal['Re-entry Pod'] = 'Re-entry Pod'
    tons: ClassVar[float]
    cost: ClassVar[float]
    _capacity: ClassVar[int] = 2

    @property
    def tons(self) -> float:
        return 1.0

    @property
    def cost(self) -> float:
        return 150_000.0

    def build_notes(self) -> list[_Note]:
        notes = NoteList(super().build_notes())
        notes.info('Includes gliding surface and computer guidance; Flyer (wing) can take manual control')
        return notes
