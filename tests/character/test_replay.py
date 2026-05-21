from ceres.character.events import CharacterStartedEvent, UcpEvent
from ceres.character.replay import ReplayError, replay


def _started(id: int = 1) -> CharacterStartedEvent:
    return CharacterStartedEvent(id=id, sophont='Vilani', player='NPC', name='Boss')


def _ucp(id: int = 2, ucp: str = '7869A5') -> UcpEvent:
    return UcpEvent(id=id, fulfills='1.0', ucp=ucp)


class TestCharacterStarted:
    def test_creates_ucp_pending_input(self):
        projection = replay(1, [_started()])

        assert len(projection.pending_inputs) == 1
        assert projection.pending_inputs[0].id == '1.0'
        assert projection.pending_inputs[0].kind == 'ucp'

    def test_ucp_pending_is_blocking(self):
        projection = replay(1, [_started()])

        assert projection.pending_inputs[0].blocking is True

    def test_sets_character_id(self):
        projection = replay(42, [_started()])

        assert projection.character_id == 42

    def test_sets_name_and_species_in_summary(self):
        projection = replay(1, [_started()])

        assert projection.summary.name == 'Boss'
        assert projection.summary.species == 'Vilani'

    def test_first_pending_input_is_ucp(self):
        projection = replay(1, [_started()])

        assert projection.pending_inputs[0].kind == 'ucp'


class TestUcpEvent:
    def test_resolves_pending_ucp(self):
        projection = replay(1, [_started(), _ucp()])

        assert projection.pending_inputs == []

    def test_sets_characteristics_from_short_form(self):
        projection = replay(1, [_started(), _ucp(ucp='7869A5')])

        assert projection.summary.characteristics == {
            'STR': 7,
            'DEX': 8,
            'END': 6,
            'INT': 9,
            'EDU': 10,
            'SOC': 5,
        }

    def test_sets_characteristics_from_max_values(self):
        projection = replay(1, [_started(), _ucp(ucp='FFFFFF')])

        assert projection.summary.characteristics == {
            'STR': 15,
            'DEX': 15,
            'END': 15,
            'INT': 15,
            'EDU': 15,
            'SOC': 15,
        }

    def test_no_pending_ucp_after_ucp_provided(self):
        projection = replay(1, [_started(), _ucp()])

        assert not any(p.kind == 'ucp' for p in projection.pending_inputs)


class TestReplayBlocking:
    def test_rejects_unrelated_event_while_ucp_pending(self):
        unrelated = UcpEvent(id=2, fulfills=None, ucp='7869A5')

        try:
            replay(1, [_started(), unrelated])
            assert False, 'Expected ReplayError'
        except ReplayError:
            pass

    def test_rejects_event_with_unknown_fulfills(self):
        wrong = UcpEvent(id=2, fulfills='99.0', ucp='7869A5')

        try:
            replay(1, [_started(), wrong])
            assert False, 'Expected ReplayError'
        except ReplayError:
            pass


class TestDeterminism:
    def test_same_events_produce_same_projection(self):
        events = [_started(), _ucp()]

        first = replay(1, events)
        second = replay(1, events)

        assert first.model_dump() == second.model_dump()

    def test_empty_events(self):
        projection = replay(1, [])

        assert projection.character_id == 1
        assert projection.pending_inputs == []
        assert projection.summary.name is None
