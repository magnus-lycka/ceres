"""Typed references to stored documents.

Integers on disk and in JSON, distinct types in Python, so a `PartyId` can
never be passed where an `ActorId` belongs. A reference may be stale: the thing
it points at can be deleted at any time, and every reader has to cope.
"""

from typing import NewType

ActorId = NewType('ActorId', int)
PartyId = NewType('PartyId', int)
SituationId = NewType('SituationId', int)

UNSAVED = 0
"""The id of a document the store has not seen yet.

Allocated ids start at 1, so this is unambiguous, and it keeps `id` a plain
`ActorId` everywhere rather than an optional one that every caller must narrow.
"""
