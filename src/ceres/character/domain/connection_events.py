from typing import Any, Literal

from pydantic import Field

from ceres.character.domain.character_state import CharacterProjection
from ceres.character.domain.characteristics import ConnectionKind
from ceres.character.input_specs import InputSpec, Reference, Select, form_int, form_str, literal
from ceres.character.mechanism.event_base import Event, EventHandlerBase
from ceres.character.mechanism.pending_input import PendingInputBase


class ConnectionsRollHandler(EventHandlerBase):
    kind: Literal['connections_roll'] = 'connections_roll'
    connection_type: ConnectionKind
    count: int

    def apply(self, projection: Any, event: Event, fulfilled_pending: Any = None) -> None:
        from ceres.character.domain.connection import make_connection

        for _ in range(self.count):
            projection.summary.connections.append(make_connection(self.connection_type))


class PendingConnectionsRoll(PendingInputBase):
    kind: Literal['connections_roll'] = 'connections_roll'
    connection_type: ConnectionKind = ConnectionKind.CONTACT
    options: list[int] = Field(default_factory=list)

    def event_from_form(self, form: Any) -> Event:
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
