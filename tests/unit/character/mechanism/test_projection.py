from collections.abc import Sequence

from ceres.character.mechanism.event_base import Event
from ceres.character.mechanism.projection import Projection, Summary


class _Summary:
    def model_dump_json(self) -> str:
        return '{"ok": true}'


class _Projection:
    pending_inputs: Sequence[object] = ()
    summary = _Summary()

    def has_blocking_pending(self) -> bool:
        return False

    def fulfill_pending(self, event: Event) -> None:
        self.fulfilled = event


def test_summary_protocol_accepts_model_dump_json_shape() -> None:
    summary: Summary = _Summary()

    assert summary.model_dump_json() == '{"ok": true}'


def test_projection_protocol_accepts_required_projection_shape() -> None:
    projection: Projection = _Projection()

    assert projection.pending_inputs == ()
    assert not projection.has_blocking_pending()
    assert projection.summary.model_dump_json() == '{"ok": true}'
