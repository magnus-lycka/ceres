"""Rule tests for the Pre-Career Events table (Core Rulebook p.17)."""

from ceres.character.domain.career.prisoner import PRISONER
from ceres.character.domain.characteristics import ConnectionKind
from ceres.character.domain.precareer.university import UniversityPreCareer
from ceres.character.domain.skills import Admin
from ceres.character.domain.sophont import VILANI
from tests.unit.character.helpers import MOCK_WORLD, CharacterDriver


def _student_rolling_event_4(ucp: str) -> CharacterDriver:
    """A first-term University student who has just rolled 4 on the Pre-Career Events table.

    UCP is STR DEX END INT EDU SOC; EDU 2 gives a single background skill.
    """
    d = CharacterDriver()
    d.start(VILANI, MOCK_WORLD)
    d.ucp(ucp)
    d.background_skills([Admin()])
    d.precareer(UniversityPreCareer, roll=12)
    d.precareer_event(4)
    return d


def _connection_kinds(d: CharacterDriver) -> list[ConnectionKind]:
    return [connection.kind for connection in d.projection.summary.connections]


class TestEvent4PrankGoesWrong:
    """Roll SOC 8+. Success: gain a Rival. Failure: gain an Enemy.

    "If you roll 2, you fail to graduate and must take the Prisoner career in
    your next term." Read as a natural 2 on the dice (RIC-028).
    """

    def test_nothing_is_gained_before_the_soc_roll(self):
        d = _student_rolling_event_4('778827')
        assert _connection_kinds(d) == []

    def test_is_not_left_as_a_manual_problem(self):
        d = _student_rolling_event_4('778827')
        d.precareer_prank_roll(8)
        assert not any('event 4' in problem for problem in d.projection.summary.problems)

    def test_success_gains_a_rival(self):
        d = _student_rolling_event_4('778827')  # SOC 7: DM+0
        d.precareer_prank_roll(8)
        assert _connection_kinds(d) == [ConnectionKind.RIVAL]

    def test_failure_gains_an_enemy(self):
        d = _student_rolling_event_4('778827')  # SOC 7: DM+0
        d.precareer_prank_roll(7)
        assert _connection_kinds(d) == [ConnectionKind.ENEMY]

    def test_soc_dm_applies_to_the_roll(self):
        d = _student_rolling_event_4('778829')  # SOC 9: DM+1, so 7 + 1 = 8
        d.precareer_prank_roll(7)
        assert _connection_kinds(d) == [ConnectionKind.RIVAL]

    def test_success_leaves_graduation_to_be_rolled(self):
        d = _student_rolling_event_4('778827')
        d.precareer_prank_roll(8)
        d.name_connection('Rival')
        d.precareer_graduation(12)
        term = d.projection.summary.precareer_terms[-1]
        assert term.completed and term.graduated

    def test_ordinary_failure_leaves_graduation_to_be_rolled(self):
        d = _student_rolling_event_4('778827')
        d.precareer_prank_roll(7)
        d.name_connection('Enemy')
        d.precareer_graduation(12)
        term = d.projection.summary.precareer_terms[-1]
        assert term.completed and term.graduated

    def test_roll_of_2_gains_an_enemy(self):
        d = _student_rolling_event_4('778827')
        d.precareer_prank_roll(2)
        assert _connection_kinds(d) == [ConnectionKind.ENEMY]

    def test_roll_of_2_fails_to_graduate(self):
        d = _student_rolling_event_4('778827')
        d.precareer_prank_roll(2)
        term = d.projection.summary.precareer_terms[-1]
        assert term.completed and not term.graduated
        assert not d.has_precareer_graduation_roll()

    def test_roll_of_2_must_take_prisoner_next_term(self):
        d = _student_rolling_event_4('778827')
        d.precareer_prank_roll(2)
        d.name_connection('Enemy')
        assert d.career_choice_options() == [PRISONER]
        assert d.precareer_choice_names() == []

    def test_modified_2_from_a_natural_3_is_an_ordinary_failure(self):
        # RIC-028: only a natural 2 sends the Traveller to prison. SOC 3 gives DM-1,
        # so a natural 3 is a modified 2: an Enemy, but graduation is still rolled.
        d = _student_rolling_event_4('778823')
        d.precareer_prank_roll(3)
        assert _connection_kinds(d) == [ConnectionKind.ENEMY]
        assert d.has_precareer_graduation_roll()


_STORY = (
    'Term 1 event (University): A supposedly harmless prank went wrong and someone got hurt, physically or emotionally.'
)
_ORIGIN = 'A supposedly harmless prank went wrong during University, term 1.'


class TestEvent4CreationHistory:
    """The creation history tells what happened to this Traveller, not what the rule could have done."""

    def test_before_the_roll_shows_the_story_and_the_outstanding_roll(self):
        d = _student_rolling_event_4('778827')
        assert d.projection.creation_history[-1] == (
            f'{_STORY} In progress: Roll SOC 8+ to gain a Rival instead of an Enemy; '
            'on a roll of 2 you also fail to graduate and must take the Prisoner career next term'
        )

    def test_success_tells_of_a_rival_only(self):
        d = _student_rolling_event_4('778827')
        d.precareer_prank_roll(8)
        d.name_connection('Gregg Rubart', note=_ORIGIN)
        assert d.projection.creation_history[-1] == (
            f'{_STORY} Fortunately, the outcome was only a future rival. Rival: Gregg Rubart — {_ORIGIN}'
        )

    def test_failure_tells_of_an_enemy_only(self):
        d = _student_rolling_event_4('778827')
        d.precareer_prank_roll(7)
        d.name_connection('Gregg Rubart', note=_ORIGIN)
        assert d.projection.creation_history[-1] == (
            f'{_STORY} The outcome was a future enemy. Enemy: Gregg Rubart — {_ORIGIN}'
        )

    def test_roll_of_2_tells_of_the_enemy_and_the_prison_sentence(self):
        d = _student_rolling_event_4('778827')
        d.precareer_prank_roll(2)
        d.name_connection('Gregg Rubart', note=_ORIGIN)
        assert d.projection.creation_history[-1] == (
            f'{_STORY} The outcome was a future enemy. '
            'You fail to graduate and must take the Prisoner career in your next term. '
            f'Enemy: Gregg Rubart — {_ORIGIN}'
        )

    def test_connection_is_noted_with_where_it_came_from_not_the_rule_text(self):
        d = _student_rolling_event_4('778827')
        d.precareer_prank_roll(8)
        assert d.connection_note_prefill() == _ORIGIN

    def test_history_never_quotes_the_outcomes_that_did_not_happen(self):
        d = _student_rolling_event_4('778827')
        d.precareer_prank_roll(8)
        d.name_connection('Gregg Rubart', note=_ORIGIN)
        history = ' '.join(d.projection.creation_history)
        assert 'Enemy' not in history
        assert 'Prisoner' not in history
        assert 'Roll SOC' not in history
