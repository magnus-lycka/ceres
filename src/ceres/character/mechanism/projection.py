from collections.abc import Sequence
from typing import TYPE_CHECKING, Any, Protocol

if TYPE_CHECKING:
    from ceres.character.mechanism.event_base import Event


class Summary(Protocol):
    def model_dump_json(self) -> str: ...


class Projection(Protocol):
    pending_inputs: Sequence[Any]

    def has_blocking_pending(self) -> bool: ...

    def fulfill_pending(self, event: Event) -> None: ...

    @property
    def summary(self) -> Summary: ...
