"""Displayed creation history, rebuilt from events rather than persisted."""

from dataclasses import dataclass, field


@dataclass
class CreationHistory:
    _entries: dict[int | str, str] = field(default_factory=dict)
    _pending: dict[int | str, list[str]] = field(default_factory=dict)

    def start(self, occurrence: int | str, description: str) -> None:
        self._entries[occurrence] = description

    def render(self) -> list[str]:
        return [
            text + (' In progress: ' + ' '.join(self._pending[key]) if self._pending.get(key) else '')
            for key, text in self._entries.items()
        ]

    def record(self, occurrence: int | str, outcome: str) -> None:
        self._entries[occurrence] += ' ' + outcome

    def continue_sentence(self, occurrence: int | str, clause: str) -> None:
        """Carry the entry's last sentence on with `clause`, e.g. '... his protégé' + 'and teaches you tactics.'"""
        self._entries[occurrence] = f'{self._entries[occurrence].removesuffix(".")} {clause}'

    def pending(self, occurrence: int | str, instructions: list[str]) -> None:
        self._pending[occurrence] = instructions
