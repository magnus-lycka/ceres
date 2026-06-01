"""Tests for CharacterProjection.skill_choices and check_skill_choice."""

from ceres.character.characteristics import ConnectionKind
from ceres.character.skills import (
    Admin,
    Animals,
    Electronics,
    Level,
    LifeScience,
    PhysicalScience,
    RoboticScience,
    SocialScience,
    SpaceScience,
)
from ceres.character.sophonts import VILANI
from ceres.character.state import (
    CharacterProjection,
    CharacterSummary,
    make_connection,
)
from tests.character.helpers import MOCK_WORLD


def _projection(skills=None) -> CharacterProjection:
    summary = CharacterSummary(name='Test', sophont=VILANI, homeworld=MOCK_WORLD, skills=skills or [])
    return CharacterProjection(character_id=1, summary=summary)


class TestCompanionConnectionRules:
    def test_ally_roll_sets_affinity_and_zero_enmity(self):
        connection = make_connection(ConnectionKind.ALLY, affinity_roll=7)

        assert connection.affinity == 3
        assert connection.enmity == 0

    def test_contact_rolls_can_be_mixed(self):
        connection = make_connection(ConnectionKind.CONTACT, affinity_roll=5, enmity_roll=2)

        assert connection.affinity == 2
        assert connection.enmity == 0

    def test_rival_can_have_affinity(self):
        connection = make_connection(ConnectionKind.RIVAL, affinity_roll=5, enmity_roll=2)

        assert connection.affinity == 2
        assert connection.enmity == 0

    def test_enemy_roll_sets_zero_affinity_and_negative_enmity(self):
        connection = make_connection(ConnectionKind.ENEMY, enmity_roll=8)

        assert connection.affinity == 0
        assert connection.enmity == -3

    def test_affinity_enmity_result_12_is_extreme_value_6(self):
        connection = make_connection(ConnectionKind.ALLY, affinity_roll=12)

        assert connection.affinity == 6


class TestSkillChoicesNonSpecialised:
    def test_missing_skill_increment_gives_level_1(self):
        proj = _projection()

        choices = proj.skill_choices([Admin], None)

        assert choices == [Admin(level=Level(value=1))]

    def test_level_0_increment_gives_level_1(self):
        proj = _projection([Admin(level=Level(value=0))])

        choices = proj.skill_choices([Admin], None)

        assert choices == [Admin(level=Level(value=1))]

    def test_level_1_increment_gives_level_2(self):
        proj = _projection([Admin(level=Level(value=1))])

        choices = proj.skill_choices([Admin], None)

        assert choices == [Admin(level=Level(value=2))]

    def test_level_3_increment_gives_level_4(self):
        proj = _projection([Admin(level=Level(value=3))])

        choices = proj.skill_choices([Admin], None)

        assert choices == [Admin(level=Level(value=4))]

    def test_level_4_increment_gives_no_choices(self):
        proj = _projection([Admin(level=Level(value=4))])

        choices = proj.skill_choices([Admin], None)

        assert choices == []

    def test_fixed_level_1_when_missing_gives_choice(self):
        proj = _projection()

        choices = proj.skill_choices([Admin], 1)

        assert choices == [Admin(level=Level(value=1))]

    def test_fixed_level_1_when_at_level_0_gives_choice(self):
        proj = _projection([Admin(level=Level(value=0))])

        choices = proj.skill_choices([Admin], 1)

        assert choices == [Admin(level=Level(value=1))]

    def test_fixed_level_1_when_already_at_level_1_gives_no_choices(self):
        proj = _projection([Admin(level=Level(value=1))])

        choices = proj.skill_choices([Admin], 1)

        assert choices == []

    def test_fixed_level_1_when_above_level_1_gives_no_choices(self):
        proj = _projection([Admin(level=Level(value=3))])

        choices = proj.skill_choices([Admin], 1)

        assert choices == []


class TestSkillChoicesSpecialised:
    def test_missing_skill_increment_gives_choices_for_all_specs(self):
        proj = _projection()

        choices = proj.skill_choices([Animals], None)

        assert Animals(handling=Level(value=1)) in choices
        assert Animals(veterinary=Level(value=1)) in choices
        assert Animals(training=Level(value=1)) in choices
        assert len(choices) == 3

    def test_spec_at_level_0_increment_gives_level_1_for_that_spec(self):
        proj = _projection([Animals(handling=Level(value=0))])

        choices = proj.skill_choices([Animals], None)

        assert Animals(handling=Level(value=1)) in choices

    def test_spec_at_level_3_increment_gives_level_4(self):
        proj = _projection([Animals(handling=Level(value=3))])

        choices = proj.skill_choices([Animals], None)

        assert Animals(handling=Level(value=4)) in choices
        assert Animals(veterinary=Level(value=1)) in choices
        assert Animals(training=Level(value=1)) in choices
        assert len(choices) == 3

    def test_spec_at_level_4_not_included_in_increment(self):
        proj = _projection([Animals(handling=Level(value=4))])

        choices = proj.skill_choices([Animals], None)

        assert not any(getattr(c, 'handling', Level(value=0)).value > 4 for c in choices)
        assert Animals(handling=Level(value=5)) not in choices
        assert Animals(veterinary=Level(value=1)) in choices
        assert Animals(training=Level(value=1)) in choices
        assert len(choices) == 2

    def test_multiple_skill_types(self):
        proj = _projection()

        choices = proj.skill_choices([LifeScience, PhysicalScience, RoboticScience, SocialScience, SpaceScience], None)

        assert len(choices) == 19  # 3+3+2+5+6 specializations across all science classes


class TestSkillChoicesMultipleTypes:
    def test_returns_choices_for_all_skill_types(self):
        proj = _projection()

        choices = proj.skill_choices([Admin, Animals], None)

        assert Admin(level=Level(value=1)) in choices
        assert Animals(handling=Level(value=1)) in choices

    def test_excludes_maxed_types(self):
        proj = _projection([Admin(level=Level(value=4))])

        choices = proj.skill_choices([Admin, Animals], None)

        assert Admin(level=Level(value=5)) not in choices
        assert Admin(level=Level(value=4)) not in choices
        assert Animals(handling=Level(value=1)) in choices


class TestCheckSkillChoice:
    def test_valid_increment_choice_returns_true(self):
        proj = _projection()

        assert proj.check_skill_choice([Admin], None, Admin(level=Level(value=1))) is True

    def test_skipping_levels_returns_false(self):
        proj = _projection()

        assert proj.check_skill_choice([Admin], None, Admin(level=Level(value=3))) is False

    def test_level_2_3_returns_true(self):
        proj = _projection([Animals(handling=Level(value=2))])

        assert proj.check_skill_choice([Animals], None, Animals(handling=Level(value=3))) is True
        assert proj.check_skill_choice([Animals], None, Animals(training=Level(value=1))) is True
        assert proj.check_skill_choice([Animals], None, Animals(veterinary=Level(value=1))) is True

    def test_level_0_for_increment_returns_false(self):
        proj = _projection()

        assert proj.check_skill_choice([Admin], None, Admin()) is False

    def test_fixed_level_0_returns_true(self):
        proj = _projection()

        assert proj.check_skill_choice([Admin], 0, Admin()) is True

    def test_valid_specialised_choice_returns_true(self):
        proj = _projection()

        result = proj.check_skill_choice(
            [LifeScience, PhysicalScience, RoboticScience, SocialScience, SpaceScience],
            None,
            SpaceScience(planetology=Level(value=1)),
        )

        assert result is True

    def test_skipping_levels_specialised_returns_false(self):
        proj = _projection()

        result = proj.check_skill_choice(
            [LifeScience, PhysicalScience, RoboticScience, SocialScience, SpaceScience],
            None,
            SpaceScience(planetology=Level(value=3)),
        )

        assert result is False

    def test_level_0_increment_specialised_returns_false(self):
        proj = _projection()

        result = proj.check_skill_choice(
            [LifeScience, PhysicalScience, RoboticScience, SocialScience, SpaceScience],
            None,
            SpaceScience(),
        )

        assert result is False

    def test_fixed_level_0_specialised_returns_true(self):
        proj = _projection()

        result = proj.check_skill_choice(
            [LifeScience, PhysicalScience, RoboticScience, SocialScience, SpaceScience],
            0,
            SpaceScience(),
        )

        assert result is True

    def test_electronics_not_in_science_types_returns_false(self):
        proj = _projection()

        result = proj.check_skill_choice(
            [LifeScience, PhysicalScience, RoboticScience, SocialScience, SpaceScience],
            None,
            Electronics(computers=Level(value=1)),
        )

        assert result is False
