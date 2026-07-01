"""Annotated snapshot support for approval tests.

Usage in a test:

    def test_something(snapshot):
        snap = AnnotatedSnapshot(build_something_dict())
        snap.annotate('cost', 'Ceres Cr860 vs source Cr500 — source uses editorial rounding')
        assert snap == snapshot(extension_class=AnnotatedJSONSnapshotExtension)

The snapshot file stores both ``data`` and ``annotations``.  Annotations come
from the test code, so they survive ``--snapshot-update`` automatically — the
update just re-serializes whatever ``annotate()`` calls are present.
"""

from collections.abc import Iterator
import json
from typing import Any

from syrupy.extensions.json import JSONSnapshotExtension
from syrupy.types import SerializedData


class AnnotatedSnapshot:
    def __init__(self, data: dict) -> None:
        self._data = data
        self._annotations: dict[str, Any] = {}

    def annotate(self, key: str, note: Any) -> AnnotatedSnapshot:
        self._annotations[key] = note
        return self

    def to_serializable(self) -> dict:
        result: dict = {'data': self._data}
        if self._annotations:
            result['annotations'] = self._annotations
        return result


def _structural_diff(old, new, path: str = '') -> list[str]:
    """Recursively find structural differences between two JSON values.

    Returns lines prefixed with '-' (snapshot only) or '+' (received only).
    Only reports the deepest level where values actually differ, so an inserted
    dict key shows as one '+' line rather than many confusing text-diff lines.
    """
    if isinstance(old, dict) and isinstance(new, dict):
        lines = []
        for key in sorted(set(old) | set(new)):
            child = f'{path}.{key}' if path else key
            if key not in old:
                lines.append(f'+   {child}: {json.dumps(new[key], ensure_ascii=False)}')
            elif key not in new:
                lines.append(f'-   {child}: {json.dumps(old[key], ensure_ascii=False)}')
            else:
                lines.extend(_structural_diff(old[key], new[key], child))
        return lines
    if isinstance(old, list) and isinstance(new, list):
        if old == new:
            return []
        if len(old) == len(new):
            lines = []
            for i, (o, n) in enumerate(zip(old, new, strict=True)):
                lines.extend(_structural_diff(o, n, f'{path}[{i}]'))
            return lines
        return [
            f'-   {path}: {json.dumps(old, ensure_ascii=False)}',
            f'+   {path}: {json.dumps(new, ensure_ascii=False)}',
        ]
    if old == new:
        return []
    return [
        f'-   {path}: {json.dumps(old, ensure_ascii=False)}',
        f'+   {path}: {json.dumps(new, ensure_ascii=False)}',
    ]


class AnnotatedJSONSnapshotExtension(JSONSnapshotExtension):
    def serialize(self, data, *, exclude=None, include=None, matcher=None) -> str:
        if isinstance(data, AnnotatedSnapshot):
            return json.dumps(data.to_serializable(), indent=2, ensure_ascii=False) + '\n'
        result = super().serialize(data, exclude=exclude, include=include, matcher=matcher)
        return result if isinstance(result, str) else result.decode()

    def diff_lines(self, serialized_data: SerializedData, snapshot_data: SerializedData) -> Iterator[str]:
        """Structural JSON diff — avoids misleading text-alignment artifacts from ndiff."""
        try:
            received = json.loads(str(serialized_data))
            stored = json.loads(str(snapshot_data))
        except json.JSONDecodeError, TypeError:
            yield from super().diff_lines(serialized_data, snapshot_data)
            return
        diff = _structural_diff(stored, received)
        yield '[- snapshot]  [+ received]'
        if diff:
            yield from diff
        else:
            yield '  (no structural differences)'
