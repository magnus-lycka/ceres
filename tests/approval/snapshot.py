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

import json

from syrupy.extensions.json import JSONSnapshotExtension


class AnnotatedSnapshot:
    def __init__(self, data: dict) -> None:
        self._data = data
        self._annotations: dict[str, str] = {}

    def annotate(self, key: str, note: str) -> AnnotatedSnapshot:
        self._annotations[key] = note
        return self

    def to_serializable(self) -> dict:
        result: dict = {'data': self._data}
        if self._annotations:
            result['annotations'] = self._annotations
        return result


class AnnotatedJSONSnapshotExtension(JSONSnapshotExtension):
    def serialize(self, data, *, exclude=None, include=None, matcher=None) -> str:
        if isinstance(data, AnnotatedSnapshot):
            return json.dumps(data.to_serializable(), indent=2, ensure_ascii=False) + '\n'
        result = super().serialize(data, exclude=exclude, include=include, matcher=matcher)
        return result if isinstance(result, str) else result.decode()
