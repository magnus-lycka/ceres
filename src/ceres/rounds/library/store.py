"""The only way in and out of stored documents.

One JSON file per document today. Callers never learn that: they hand over and
receive Pydantic models, so the store can become a database without anything
above it noticing.

Deletion is unguarded. Nothing checks whether a document is referenced, because
a single-user tool has no business arguing with its user about it. What the
store owes instead is that a stale reference resolves to nothing rather than
raising — the same bargain as ON DELETE SET NULL.
"""

import json
from pathlib import Path

from ceres.rounds.library.ids import UNSAVED, ActorId, PartyId, SituationId
from ceres.rounds.library.models import Actor, Party, Situation

type Document = Actor | Party | Situation

DIRECTORIES: dict[type[Document], str] = {Actor: 'actors', Party: 'parties', Situation: 'situations'}
"""Where each kind of document lives, which is the store's business alone."""


class Library:
    """Actors, Parties and Situations, kept somewhere the caller cannot see."""

    def __init__(self, root: Path):
        self._root = root

    def actors(self) -> list[Actor]:
        return self._all(Actor)

    def actor(self, actor_id: ActorId) -> Actor | None:
        """None when it has been deleted, which callers must expect."""
        return self._one(Actor, actor_id)

    def save_actor(self, actor: Actor) -> Actor:
        return self._save(actor)

    def delete_actor(self, actor_id: ActorId) -> None:
        self._delete(Actor, actor_id)

    def parties(self) -> list[Party]:
        return self._all(Party)

    def party(self, party_id: PartyId) -> Party | None:
        return self._one(Party, party_id)

    def save_party(self, party: Party) -> Party:
        return self._save(party)

    def delete_party(self, party_id: PartyId) -> None:
        self._delete(Party, party_id)

    def party_members(self, party_id: PartyId) -> list[Actor | None]:
        """The members in stored order, with a hole where one has been deleted."""
        party = self.party(party_id)
        return [self.actor(actor_id) for actor_id in party.actors] if party else []

    def situations(self) -> list[Situation]:
        return self._all(Situation)

    def situation(self, situation_id: SituationId) -> Situation | None:
        return self._one(Situation, situation_id)

    def save_situation(self, situation: Situation) -> Situation:
        return self._save(situation)

    def delete_situation(self, situation_id: SituationId) -> None:
        self._delete(Situation, situation_id)

    def add_party_to_situation(self, situation_id: SituationId, party_id: PartyId) -> Situation:
        """Copy a Party in, and forget it.

        The name and the members it holds at this moment become rows of the
        Situation's own. Nothing links the two afterwards in either direction.
        """
        situation = self.situation(situation_id)
        party = self.party(party_id)
        if situation is None or party is None:
            msg = 'situation and party must both still exist'
            raise LookupError(msg)
        for actor_id in party.actors:
            situation.members.append(situation.member_for(actor_id, party=party.name))
        return self.save_situation(situation)

    def _all[D: (Actor, Party, Situation)](self, kind: type[D]) -> list[D]:
        return [kind.model_validate_json(path.read_text()) for path in sorted(self._paths(kind))]

    def _one[D: (Actor, Party, Situation)](self, kind: type[D], key: int) -> D | None:
        path = self._path(kind, key)
        return kind.model_validate_json(path.read_text()) if path.exists() else None

    def _save[D: (Actor, Party, Situation)](self, document: D) -> D:
        if document.id == UNSAVED:
            document = document.model_copy(update={'id': self._next_id(type(document))})
        path = self._path(type(document), document.id)
        path.parent.mkdir(parents=True, exist_ok=True)
        self._write(path, document.model_dump(mode='json'))
        return document

    def _delete[D: (Actor, Party, Situation)](self, kind: type[D], key: int) -> None:
        self._path(kind, key).unlink(missing_ok=True)

    def _next_id(self, kind: type[Document]) -> int:
        """Ids only ever climb, so a deleted one is never handed out again."""
        counters = self._counters()
        highest = max([int(path.stem) for path in self._paths(kind)], default=0)
        allocated = max(counters.get(kind.__name__, 0), highest) + 1
        counters[kind.__name__] = allocated
        self._root.mkdir(parents=True, exist_ok=True)
        self._write(self._counters_file, counters)
        return allocated

    def _counters(self) -> dict[str, int]:
        return json.loads(self._counters_file.read_text()) if self._counters_file.exists() else {}

    @property
    def _counters_file(self) -> Path:
        return self._root / 'counters.json'

    def _paths(self, kind: type[Document]) -> list[Path]:
        directory = self._directory(kind)
        return list(directory.glob('*.json')) if directory.exists() else []

    def _path(self, kind: type[Document], key: int) -> Path:
        return self._directory(kind) / f'{key}.json'

    def _directory(self, kind: type[Document]) -> Path:
        return self._root / DIRECTORIES[kind]

    @staticmethod
    def _write(path: Path, content: dict) -> None:
        """Atomic, so a crash mid-write cannot leave half a document behind."""
        temporary = path.with_suffix('.json.tmp')
        temporary.write_text(json.dumps(content, indent=2, ensure_ascii=False) + '\n')
        temporary.replace(path)
