"""What the parties grid shows, and what a stale reference looks like in it.

The row builders are ordinary functions so they can be tested without a
browser: AG Grid renders client-side, so the in-process test user sees no cell
content at all, and anything read back through `get_selected_rows()` is a
JavaScript round trip that times out in tests. Selection is therefore mirrored
in Python, and everything worth asserting lives in these functions.
"""

import pytest

from ceres.rounds.library.models import Actor, ActorKind, Party
from ceres.rounds.library.store import Library
from ceres.rounds.ui.parties import MISSING, known_tags, member_rows, party_rows, row_id


@pytest.fixture
def library(tmp_path) -> Library:
    return Library(tmp_path)


def test_a_party_row_counts_its_actors(library):
    rin = library.save_actor(Actor(name='Rin', kind=ActorKind.SOPHONT, strength=8, dexterity=8, endurance=8))
    wolf = library.save_actor(Actor(name='Wolf', kind=ActorKind.ANIMAL, hits=12))
    library.save_party(Party(name='Crew', note='the PCs', tags=['pc', 'ship'], actors=[rin.id, wolf.id]))

    assert party_rows(library) == [{'id': 1, 'name': 'Crew', 'members': 2, 'tags': 'pc ship', 'note': 'the PCs'}]


def test_member_rows_show_each_kind_in_its_own_columns(library):
    rin = library.save_actor(Actor(name='Rin', kind=ActorKind.SOPHONT, strength=8, dexterity=7, endurance=6))
    wolf = library.save_actor(Actor(name='Wolf', kind=ActorKind.ANIMAL, hits=12, tags=['beast']))
    party = library.save_party(Party(name='Crew', actors=[rin.id, wolf.id]))

    rows = member_rows(library, party.id)

    assert rows[0] == {'id': 1, 'name': 'Rin', 'kind': 'sophont', 'STR': 8, 'DEX': 7, 'END': 6, 'tags': ''}
    assert rows[1] == {
        'id': 2,
        'name': 'Wolf',
        'kind': 'animal',
        'STR': MISSING,
        'DEX': MISSING,
        'END': MISSING,
        'tags': 'beast',
    }


def test_a_deleted_actor_leaves_a_row_of_dashes_rather_than_disappearing(library):
    rin = library.save_actor(Actor(name='Rin', kind=ActorKind.SOPHONT, strength=8, dexterity=8, endurance=8))
    sana = library.save_actor(Actor(name='Sana', kind=ActorKind.SOPHONT, strength=6, dexterity=9, endurance=7))
    party = library.save_party(Party(name='Crew', actors=[rin.id, sana.id]))

    library.delete_actor(rin.id)

    rows = member_rows(library, party.id)
    assert rows[0] == {
        'id': 1,
        'name': MISSING,
        'kind': MISSING,
        'STR': MISSING,
        'DEX': MISSING,
        'END': MISSING,
        'tags': MISSING,
    }
    assert rows[1]['name'] == 'Sana'


def test_no_party_selected_means_no_members(library):
    assert member_rows(library, None) == []


def test_a_deleted_party_shows_no_members_rather_than_failing(library):
    party = library.save_party(Party(name='Crew'))

    library.delete_party(party.id)

    assert member_rows(library, party.id) == []


class TestTags:
    """Tags are a list, offered as suggestions and used to narrow the grid."""

    def party(self, library: Library, name: str, *tags: str) -> None:
        library.save_party(Party(name=name, tags=list(tags)))

    def test_every_tag_in_use_is_offered_as_a_suggestion(self, library):
        self.party(library, 'Crew', 'pc', 'marduk')
        self.party(library, 'Warbots', 'marduk')

        assert known_tags(library) == ['marduk', 'pc']

    def test_no_tags_selected_shows_everything(self, library):
        self.party(library, 'Crew', 'pc')
        self.party(library, 'Warbots', 'marduk')

        assert [row['name'] for row in party_rows(library)] == ['Crew', 'Warbots']

    def test_a_tag_narrows_the_grid_to_the_parties_carrying_it(self, library):
        self.party(library, 'Crew', 'pc', 'marduk')
        self.party(library, 'Warbots', 'marduk')
        self.party(library, 'Pirates')

        assert [row['name'] for row in party_rows(library, tags=['marduk'])] == ['Crew', 'Warbots']

    def test_several_tags_narrow_further_rather_than_widening(self, library):
        """Picking a second tag asks for both, which is what narrowing means."""
        self.party(library, 'Crew', 'pc', 'marduk')
        self.party(library, 'Warbots', 'marduk')

        assert [row['name'] for row in party_rows(library, tags=['marduk', 'pc'])] == ['Crew']


class TestRowIdFromGridEvents:
    """Grid payloads are untrusted: keys AG Grid appears to promise go missing."""

    def test_the_row_a_normal_event_is_about(self):
        assert row_id({'data': {'id': 3}, 'selected': True}) == 3

    def test_an_event_with_no_row_names_nobody(self):
        assert row_id({}) is None
        assert row_id({'data': None}) is None
        assert row_id({'data': {}}) is None
