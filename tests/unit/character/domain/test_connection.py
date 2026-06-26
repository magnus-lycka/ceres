"""Unit tests for connection.py — Contact, Ally, Rival, Enemy, make_connection."""

from ceres.character.domain.characteristics import ConnectionKind
from ceres.character.domain.connection import Ally, Contact, Enemy, Rival, make_connection


class TestConnectionDisplayName:
    def test_contact(self):
        assert Contact().display_name == 'Contact'

    def test_ally(self):
        assert Ally().display_name == 'Ally'

    def test_rival(self):
        assert Rival().display_name == 'Rival'

    def test_enemy(self):
        assert Enemy().display_name == 'Enemy'


class TestConnectionFields:
    def test_name_default_empty(self):
        assert Contact().name == ''

    def test_stores_term(self):
        assert Ally(term=3).term == 3

    def test_stores_origin(self):
        assert Rival(origin='battleground').origin == 'battleground'

    def test_stores_note(self):
        assert Enemy(note='watch out').note == 'watch out'


class TestMakeConnection:
    def test_contact_kind(self):
        c = make_connection(ConnectionKind.CONTACT)
        assert isinstance(c, Contact)

    def test_ally_kind(self):
        c = make_connection(ConnectionKind.ALLY)
        assert isinstance(c, Ally)

    def test_rival_kind(self):
        c = make_connection(ConnectionKind.RIVAL)
        assert isinstance(c, Rival)

    def test_enemy_kind(self):
        c = make_connection(ConnectionKind.ENEMY)
        assert isinstance(c, Enemy)

    def test_passes_term(self):
        c = make_connection(ConnectionKind.ALLY, term=2)
        assert c.term == 2

    def test_passes_origin(self):
        c = make_connection(ConnectionKind.CONTACT, origin='scout')
        assert c.origin == 'scout'
