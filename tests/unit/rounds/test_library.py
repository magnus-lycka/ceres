"""The stored library: Actors, Parties, Situations, and stale references.

Deletion is unguarded on purpose — this is a single-user tool. What the code
owes in return is that nothing breaks when a reference points at something that
is no longer there: an absent Actor resolves to nothing, the way a foreign key
with ON DELETE SET NULL does, and whatever local facts the referrer holds of
its own survive untouched.
"""

import json

from pydantic import ValidationError
import pytest

from ceres.rounds.library.ids import ActorId
from ceres.rounds.library.models import Actor, ActorKind, Party, Situation
from ceres.rounds.library.store import Library


@pytest.fixture
def library(tmp_path) -> Library:
    return Library(tmp_path)


def sophont(name: str = 'Rin', *, tags: list[str] | None = None) -> Actor:
    return Actor(name=name, kind=ActorKind.SOPHONT, strength=8, dexterity=8, endurance=8, tags=tags or [])


class TestActorDocuments:
    def test_saving_allocates_an_id_and_reading_it_back_gives_the_same_actor(self, library):
        saved = library.save_actor(sophont(tags=['crew']))

        assert saved.id == 1
        assert library.actor(saved.id) == saved

    def test_ids_keep_climbing_so_a_deleted_one_is_never_reused(self, library):
        first = library.save_actor(sophont('Rin'))
        second = library.save_actor(sophont('Sana'))
        library.delete_actor(second.id)

        third = library.save_actor(sophont('Kes'))

        assert (first.id, second.id, third.id) == (1, 2, 3)

    def test_saving_an_actor_that_has_an_id_replaces_it(self, library):
        saved = library.save_actor(sophont('Rin'))

        library.save_actor(saved.model_copy(update={'name': 'Rin Kaur'}))

        assert [actor.name for actor in library.actors()] == ['Rin Kaur']

    def test_a_sophont_needs_its_three_physical_characteristics(self):
        with pytest.raises(ValidationError):
            Actor(name='Rin', kind=ActorKind.SOPHONT)

    def test_an_animal_needs_hits(self):
        with pytest.raises(ValidationError):
            Actor(name='Wolf', kind=ActorKind.ANIMAL)

    def test_an_animal_has_no_characteristics_to_give(self):
        with pytest.raises(ValidationError):
            Actor(name='Wolf', kind=ActorKind.ANIMAL, hits=12, strength=4)


class TestPartyDocuments:
    def test_a_party_holds_its_members_by_reference(self, library):
        rin = library.save_actor(sophont('Rin'))
        sana = library.save_actor(sophont('Sana'))

        party = library.save_party(Party(name='Crew', note='the PCs', tags=['pc'], actors=[rin.id, sana.id]))

        assert library.party(party.id).actors == [rin.id, sana.id]
        assert [actor.name for actor in library.party_members(party.id)] == ['Rin', 'Sana']

    def test_deleting_a_member_leaves_the_party_standing_with_a_hole(self, library):
        rin = library.save_actor(sophont('Rin'))
        sana = library.save_actor(sophont('Sana'))
        party = library.save_party(Party(name='Crew', actors=[rin.id, sana.id]))

        library.delete_actor(rin.id)

        assert library.party(party.id).actors == [rin.id, sana.id]
        assert [actor and actor.name for actor in library.party_members(party.id)] == [None, 'Sana']

    def test_a_missing_actor_resolves_to_nothing_rather_than_raising(self, library):
        assert library.actor(ActorId(404)) is None

    def test_deleting_a_party_touches_nothing_else(self, library):
        rin = library.save_actor(sophont('Rin'))
        party = library.save_party(Party(name='Crew', actors=[rin.id]))

        library.delete_party(party.id)

        assert library.parties() == []
        assert library.actor(rin.id) is not None


class TestSituationDocuments:
    def test_a_situation_copies_a_party_rather_than_referring_to_it(self, library):
        rin = library.save_actor(sophont('Rin'))
        sana = library.save_actor(sophont('Sana'))
        party = library.save_party(Party(name='Raiders', actors=[rin.id, sana.id]))
        situation = library.save_situation(Situation(name='Cargo bay'))

        situation = library.add_party_to_situation(situation.id, party.id)

        assert [(member.actor, member.party) for member in situation.members] == [
            (rin.id, 'Raiders'),
            (sana.id, 'Raiders'),
        ]

    def test_changing_the_party_afterwards_leaves_the_situation_alone(self, library):
        rin = library.save_actor(sophont('Rin'))
        party = library.save_party(Party(name='Raiders', actors=[rin.id]))
        situation = library.add_party_to_situation(library.save_situation(Situation(name='Bay')).id, party.id)

        library.save_party(library.party(party.id).model_copy(update={'name': 'Pirates', 'actors': []}))

        assert [member.party for member in library.situation(situation.id).members] == ['Raiders']

    def test_deleting_the_party_leaves_the_situation_alone(self, library):
        rin = library.save_actor(sophont('Rin'))
        party = library.save_party(Party(name='Raiders', actors=[rin.id]))
        situation = library.add_party_to_situation(library.save_situation(Situation(name='Bay')).id, party.id)

        library.delete_party(party.id)

        assert [member.party for member in library.situation(situation.id).members] == ['Raiders']

    def test_a_deleted_actor_leaves_its_row_and_the_facts_the_row_owns(self, library):
        rin = library.save_actor(sophont('Rin'))
        situation = library.save_situation(Situation(name='Bay'))
        situation.members.append(situation.member_for(rin.id, party='Crew'))
        situation.members[0].initiative = 7
        library.save_situation(situation)

        library.delete_actor(rin.id)

        row = library.situation(situation.id).members[0]
        assert row.actor == rin.id
        assert (row.party, row.initiative) == ('Crew', 7)
        assert library.actor(row.actor) is None


class TestStorageStaysBehindTheService:
    def test_documents_survive_a_new_library_over_the_same_directory(self, tmp_path):
        first = Library(tmp_path)
        rin = first.save_actor(sophont('Rin'))
        first.save_party(Party(name='Crew', actors=[rin.id]))

        second = Library(tmp_path)

        assert [actor.name for actor in second.actors()] == ['Rin']
        assert [party.name for party in second.parties()] == ['Crew']

    def test_a_document_is_readable_json_on_disk(self, tmp_path):
        library = Library(tmp_path)

        rin = library.save_actor(sophont('Rin', tags=['pc']))

        written = json.loads(next(tmp_path.rglob(f'{rin.id}.json')).read_text())
        assert written['name'] == 'Rin'
        assert written['tags'] == ['pc']

    def test_the_service_exposes_no_paths(self):
        """Callers must not learn where documents live, so this can change."""
        leaks = [name for name in vars(Library) if 'path' in name.lower() or 'file' in name.lower()]
        assert [name for name in leaks if not name.startswith('_')] == []
