from collections.abc import Mapping
from typing import Literal

from pydantic import Field

from ceres.character.domain.character_state import CharacterProjection
from ceres.character.domain.characteristics import ConnectionKind
from ceres.character.input_specs import InputSpec, Reference, Select, TextEntry, form_int, form_str, literal
from ceres.character.mechanism.event_base import Event, EventHandlerBase
from ceres.character.mechanism.pending_input import PendingInputBase


class ConnectionsRollHandler(EventHandlerBase):
    kind: Literal['connections_roll'] = 'connections_roll'
    connection_type: ConnectionKind
    count: int
    origin: str = ''

    def apply(
        self, projection: CharacterProjection, event: Event, fulfilled_pending: PendingInputBase | None = None
    ) -> None:
        for _ in range(self.count):
            projection.add_connection(self.connection_type, origin=self.origin)


class PendingConnectionsRoll(PendingInputBase):
    kind: Literal['connections_roll'] = 'connections_roll'
    connection_type: ConnectionKind = ConnectionKind.CONTACT
    options: list[int] = Field(default_factory=list)
    origin: str = ''

    def event_from_form(self, form: Mapping[str, str]) -> Event:
        raw_connection_type = literal(
            form_str(form, 'connection_type', ConnectionKind.CONTACT),
            tuple(ConnectionKind),
            ConnectionKind.CONTACT,
        )
        return Event(
            fulfills=self.pending_id,
            handler=ConnectionsRollHandler(
                connection_type=ConnectionKind(raw_connection_type),
                count=form_int(form, 'count', 1),
                origin=self.origin,
            ),
        )

    def input_specs(self, projection: CharacterProjection) -> list[InputSpec]:
        count_options = (
            [(str(option), str(option)) for option in self.options]
            if self.options
            else [(str(value), str(value)) for value in range(1, 7)]
        )
        return [
            Reference(name='connection_type', value=self.connection_type.value),
            Select(name='count', label='Count', options=count_options),
        ]


class ConnectionNameHandler(EventHandlerBase):
    kind: Literal['connection_name'] = 'connection_name'
    connection_index: int
    name: str = ''
    note: str = ''

    def apply(
        self, projection: CharacterProjection, event: Event, fulfilled_pending: PendingInputBase | None = None
    ) -> None:
        conn = projection.summary.connections[self.connection_index]
        conn.name = self.name
        conn.note = self.note


class PendingConnectionName(PendingInputBase):
    kind: Literal['connection_name'] = 'connection_name'
    blocking: bool = False
    connection_index: int
    connection_kind: ConnectionKind
    note_prefill: str = ''

    def event_from_form(self, form: Mapping[str, str]) -> Event:
        return Event(
            fulfills=self.pending_id,
            handler=ConnectionNameHandler(
                connection_index=self.connection_index,
                name=form_str(form, 'name', ''),
                note=form_str(form, 'note', ''),
            ),
        )

    def input_specs(self, projection: CharacterProjection) -> list[InputSpec]:
        kind_label = self.connection_kind.value.replace('connection_', '').title()
        return [
            TextEntry(name='name', label=f'{kind_label} name', placeholder='e.g. Agent Vessa Koh'),
            TextEntry(name='note', label='Note', value=self.note_prefill, multiline=True),
        ]
