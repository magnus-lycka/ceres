"""Tests for precareer entry and graduation (core University and Mongoose Traveller Companion precareers)."""

from ceres.character.domain.career.career_events import PendingCareerChoice
from ceres.character.domain.character_start import CharacterStartedHandler, UcpHandler
from ceres.character.domain.characteristics import Chars
from ceres.character.domain.connection import Enemy, Rival
from ceres.character.domain.precareer.precareer_events import (
    PendingPreCareerEvent,
    PendingPreCareerGraduation,
    PendingPreCareerSkillChoice,
    PreCareerEntryHandler,
    PreCareerEventHandler,
    PreCareerGraduationHandler,
    PreCareerSkillChoiceHandler,
)
from ceres.character.domain.skills import (
    Admin,
    Astrogation,
    Athletics,
    ColonistProfession,
    Deception,
    Drive,
    Electronics,
    GunCombat,
    Level,
    LifeScience,
    PhysicalScience,
    SpaceScience,
    Streetwise,
    _level_fields,
)
from ceres.character.domain.sophont import HUMANITI
from ceres.character.mechanism.event_base import Event
from ceres.character.mechanism.replay import replay
from tests.character.helpers import MOCK_WORLD


def _base():
    """Character with EDU=0 (no background skills) and all other stats at 7."""
    return [
        Event(
            id=1, handler=CharacterStartedHandler(sophont=HUMANITI, homeworld=MOCK_WORLD, player='Test', name='Tester')
        ),
        Event(id=2, fulfills=(1, 0), handler=UcpHandler(ucp='777707')),  # STR=7 DEX=7 END=7 INT=7 EDU=0 SOC=7
    ]


def _skill_level(projection, name: str) -> int:
    """Highest level of a named skill in the projection, or -1 if absent."""
    skill = next((s for s in projection.summary.skills if type(s).name() == name), None)
    if skill is None:
        return -1
    fields = _level_fields(type(skill))
    return max((getattr(skill, f).value for f in fields), default=0)


# ── Colonial Upbringing ───────────────────────────────────────────────────────


class TestColonialUpbringing:
    def test_entry_auto_grants_nine_concrete_level_zero_skills(self):
        # 'Profession' is a broad skill category — it becomes a pending pick, not auto-granted
        events = [*_base(), Event(id=3, handler=PreCareerEntryHandler(precareer='Colonial Upbringing', roll=5))]
        projection = replay(1, events)

        for name in (
            'Animals',
            'Athletics',
            'Drive',
            'Gun Combat',
            'Mechanic',
            'Medic',
            'Navigation',
            'Recon',
            'Seafarer',
        ):
            assert _skill_level(projection, name) >= 0, f'{name} should be auto-granted at entry'

    def test_entry_auto_grants_survival_at_level_one(self):
        events = [*_base(), Event(id=3, handler=PreCareerEntryHandler(precareer='Colonial Upbringing', roll=5))]
        projection = replay(1, events)

        assert _skill_level(projection, 'Survival') >= 1

    def test_entry_queues_one_skill_pick_for_profession_category(self):
        # 'Profession' in the Colonial skill list is a category; player must pick a specialisation
        events = [*_base(), Event(id=3, handler=PreCareerEntryHandler(precareer='Colonial Upbringing', roll=5))]
        projection = replay(1, events)

        picks = [p for p in projection.pending_inputs if isinstance(p, PendingPreCareerSkillChoice)]
        assert len(picks) == 1
        assert picks[0].level == 0
        assert any(isinstance(o, ColonistProfession) for o in picks[0].options)

    def test_entry_queues_event_and_graduation_pendings(self):
        events = [*_base(), Event(id=3, handler=PreCareerEntryHandler(precareer='Colonial Upbringing', roll=5))]
        projection = replay(1, events)

        assert any(isinstance(p, PendingPreCareerEvent) for p in projection.pending_inputs)
        assert any(isinstance(p, PendingPreCareerGraduation) for p in projection.pending_inputs)

    def test_graduation_grants_jack_of_all_trades_at_level_one(self):
        # Pending IDs: '3.0' = Profession pick, '3.1' = event, '3.2' = graduation
        events = [
            *_base(),
            Event(id=3, handler=PreCareerEntryHandler(precareer='Colonial Upbringing', roll=5)),
            Event(id=4, fulfills=(3, 0), handler=PreCareerSkillChoiceHandler(skill=ColonistProfession())),
            Event(id=5, fulfills=(3, 1), handler=PreCareerEventHandler(roll=5)),
            Event(id=6, fulfills=(3, 2), handler=PreCareerGraduationHandler(roll=10)),  # effective=10>=8, no honours
        ]
        projection = replay(1, events)

        assert _skill_level(projection, 'Jack-of-All-Trades') >= 1

    def test_graduation_increases_end_by_one(self):
        events = [
            *_base(),
            Event(id=3, handler=PreCareerEntryHandler(precareer='Colonial Upbringing', roll=5)),
            Event(id=4, fulfills=(3, 0), handler=PreCareerSkillChoiceHandler(skill=ColonistProfession())),
            Event(id=5, fulfills=(3, 1), handler=PreCareerEventHandler(roll=5)),
            Event(id=6, fulfills=(3, 2), handler=PreCareerGraduationHandler(roll=10)),
        ]
        projection = replay(1, events)

        assert projection.summary.characteristics[Chars.END] == 8  # 7+1

    def test_graduation_queues_three_skill_picks_at_level_one(self):
        events = [
            *_base(),
            Event(id=3, handler=PreCareerEntryHandler(precareer='Colonial Upbringing', roll=5)),
            Event(id=4, fulfills=(3, 0), handler=PreCareerSkillChoiceHandler(skill=ColonistProfession())),
            Event(id=5, fulfills=(3, 1), handler=PreCareerEventHandler(roll=5)),
            Event(id=6, fulfills=(3, 2), handler=PreCareerGraduationHandler(roll=10)),
        ]
        projection = replay(1, events)

        picks = [p for p in projection.pending_inputs if isinstance(p, PendingPreCareerSkillChoice)]
        assert len(picks) == 3
        assert all(p.level == 1 for p in picks)

    def test_graduation_queues_career_choice_with_distinct_id(self):
        events = [
            *_base(),
            Event(id=3, handler=PreCareerEntryHandler(precareer='Colonial Upbringing', roll=5)),
            Event(id=4, fulfills=(3, 0), handler=PreCareerSkillChoiceHandler(skill=ColonistProfession())),
            Event(id=5, fulfills=(3, 1), handler=PreCareerEventHandler(roll=5)),
            Event(id=6, fulfills=(3, 2), handler=PreCareerGraduationHandler(roll=10)),
        ]
        projection = replay(1, events)

        career_choices = [p for p in projection.pending_inputs if isinstance(p, PendingCareerChoice)]
        assert len(career_choices) == 1
        pick_ids = {p.id for p in projection.pending_inputs if isinstance(p, PendingPreCareerSkillChoice)}
        assert career_choices[0].id not in pick_ids

    def test_graduation_adds_edu_and_age_problem_messages(self):
        events = [
            *_base(),
            Event(id=3, handler=PreCareerEntryHandler(precareer='Colonial Upbringing', roll=5)),
            Event(id=4, fulfills=(3, 0), handler=PreCareerSkillChoiceHandler(skill=ColonistProfession())),
            Event(id=5, fulfills=(3, 1), handler=PreCareerEventHandler(roll=5)),
            Event(id=6, fulfills=(3, 2), handler=PreCareerGraduationHandler(roll=10)),
        ]
        projection = replay(1, events)

        combined = ' '.join(projection.summary.problems)
        assert 'EDU' in combined
        assert 'age' in combined.lower()

    def test_honours_graduation_grants_leadership_and_extra_pick(self):
        events = [
            *_base(),
            Event(id=3, handler=PreCareerEntryHandler(precareer='Colonial Upbringing', roll=5)),
            Event(id=4, fulfills=(3, 0), handler=PreCareerSkillChoiceHandler(skill=ColonistProfession())),
            Event(id=5, fulfills=(3, 1), handler=PreCareerEventHandler(roll=5)),
            Event(id=6, fulfills=(3, 2), handler=PreCareerGraduationHandler(roll=12)),  # effective=12>=12, honours
        ]
        projection = replay(1, events)

        assert _skill_level(projection, 'Leadership') >= 1
        picks = [p for p in projection.pending_inputs if isinstance(p, PendingPreCareerSkillChoice)]
        assert len(picks) == 4  # 3 regular + 1 honours

    def test_graduation_pick_options_expand_specialized_skills_to_specs(self):
        # Gun Combat is a specialized skill — at level 1, the player must choose a spec,
        # so the option should appear as 'Gun Combat (Archaic)' etc., not bare 'Gun Combat'.
        events = [
            *_base(),
            Event(id=3, handler=PreCareerEntryHandler(precareer='Colonial Upbringing', roll=5)),
            Event(id=4, fulfills=(3, 0), handler=PreCareerSkillChoiceHandler(skill=ColonistProfession())),
            Event(id=5, fulfills=(3, 1), handler=PreCareerEventHandler(roll=5)),
            Event(id=6, fulfills=(3, 2), handler=PreCareerGraduationHandler(roll=10)),
        ]
        projection = replay(1, events)
        pick = next(p for p in projection.pending_inputs if isinstance(p, PendingPreCareerSkillChoice))
        from ceres.character.input_specs import Select

        spec = pick.input_specs(projection)[0]
        assert isinstance(spec, Select)
        labels = [label for label, _ in spec.options]
        assert 'Gun Combat' not in labels, 'bare specialised skill name must not appear at level 1'
        assert any(label.startswith('Gun Combat (') for label in labels)

    def test_graduation_specialized_skill_pick_gives_level_one(self):
        # Choosing 'Gun Combat (Slug)' at graduation must result in Gun Combat Slug 1,
        # even though Gun Combat 0 was already granted at entry.

        events = [
            *_base(),
            Event(id=3, handler=PreCareerEntryHandler(precareer='Colonial Upbringing', roll=5)),
            Event(id=4, fulfills=(3, 0), handler=PreCareerSkillChoiceHandler(skill=ColonistProfession())),
            Event(id=5, fulfills=(3, 1), handler=PreCareerEventHandler(roll=5)),
            Event(id=6, fulfills=(3, 2), handler=PreCareerGraduationHandler(roll=10)),
            Event(id=7, fulfills=(6, 0), handler=PreCareerSkillChoiceHandler(skill=GunCombat(slug=Level(value=1)))),
        ]
        projection = replay(1, events)
        gc = next((s for s in projection.summary.skills if isinstance(s, GunCombat)), None)
        assert gc is not None
        assert gc.slug.value == 1
        assert gc.energy.value == 0
        assert gc.archaic.value == 0

    def test_honours_career_choice_id_distinct_from_four_picks(self):
        events = [
            *_base(),
            Event(id=3, handler=PreCareerEntryHandler(precareer='Colonial Upbringing', roll=5)),
            Event(id=4, fulfills=(3, 0), handler=PreCareerSkillChoiceHandler(skill=ColonistProfession())),
            Event(id=5, fulfills=(3, 1), handler=PreCareerEventHandler(roll=5)),
            Event(id=6, fulfills=(3, 2), handler=PreCareerGraduationHandler(roll=12)),
        ]
        projection = replay(1, events)

        career_choices = [p for p in projection.pending_inputs if isinstance(p, PendingCareerChoice)]
        pick_ids = {p.id for p in projection.pending_inputs if isinstance(p, PendingPreCareerSkillChoice)}
        assert len(career_choices) == 1
        assert career_choices[0].id not in pick_ids


# ── Merchant Academy ─────────────────────────────────────────────────────────


class TestMerchantAcademy:
    def test_entry_business_grants_broker_table_skills_at_level_zero(self):
        events = [
            *_base(),
            Event(id=3, handler=PreCareerEntryHandler(precareer='Merchant Academy (Business)', roll=12)),
        ]
        projection = replay(1, events)

        for name in ('Admin', 'Advocate', 'Broker', 'Streetwise', 'Deception', 'Persuade'):
            assert _skill_level(projection, name) >= 0, f'{name} should be granted at level 0'

    def test_entry_shipboard_grants_merchant_marine_skills_at_level_zero(self):
        events = [
            *_base(),
            Event(id=3, handler=PreCareerEntryHandler(precareer='Merchant Academy (Shipboard)', roll=12)),
        ]
        projection = replay(1, events)

        for name in ('Pilot', 'Vacc Suit', 'Athletics', 'Mechanic', 'Engineer', 'Electronics'):
            assert _skill_level(projection, name) >= 0, f'{name} should be granted at level 0'

    def test_entry_queues_one_service_skill_pick_at_level_one(self):
        events = [
            *_base(),
            Event(id=3, handler=PreCareerEntryHandler(precareer='Merchant Academy (Business)', roll=12)),
        ]
        projection = replay(1, events)

        picks = [p for p in projection.pending_inputs if isinstance(p, PendingPreCareerSkillChoice)]
        assert len(picks) == 1
        assert picks[0].level == 1

    def test_entry_service_skill_options_are_merchant_service_skills(self):
        events = [
            *_base(),
            Event(id=3, handler=PreCareerEntryHandler(precareer='Merchant Academy (Business)', roll=12)),
        ]
        projection = replay(1, events)

        picks = [p for p in projection.pending_inputs if isinstance(p, PendingPreCareerSkillChoice)]
        assert any(isinstance(o, Drive) for o in picks[0].options)

    def test_shipboard_entry_grants_pilot_not_broker_skills(self):
        events = [
            *_base(),
            Event(id=3, handler=PreCareerEntryHandler(precareer='Merchant Academy (Shipboard)', roll=12)),
        ]
        projection = replay(1, events)

        assert _skill_level(projection, 'Pilot') >= 0
        assert _skill_level(projection, 'Broker') == -1

    def test_graduation_increases_edu_by_one(self):
        events = [
            *_base(),
            Event(id=3, handler=PreCareerEntryHandler(precareer='Merchant Academy (Business)', roll=12)),
            Event(id=4, fulfills=(3, 0), handler=PreCareerSkillChoiceHandler(skill=Drive())),
            Event(id=5, fulfills=(3, 1), handler=PreCareerEventHandler(roll=5)),
            Event(id=6, fulfills=(3, 2), handler=PreCareerGraduationHandler(roll=9)),  # effective=9>=7, no honours
        ]
        projection = replay(1, events)

        assert projection.summary.characteristics[Chars.EDU] == 1  # 0+1

    def test_graduation_queues_one_curriculum_skill_pick_at_level_one(self):
        events = [
            *_base(),
            Event(id=3, handler=PreCareerEntryHandler(precareer='Merchant Academy (Business)', roll=12)),
            Event(id=4, fulfills=(3, 0), handler=PreCareerSkillChoiceHandler(skill=Drive())),
            Event(id=5, fulfills=(3, 1), handler=PreCareerEventHandler(roll=5)),
            Event(id=6, fulfills=(3, 2), handler=PreCareerGraduationHandler(roll=9)),
        ]
        projection = replay(1, events)

        picks = [p for p in projection.pending_inputs if isinstance(p, PendingPreCareerSkillChoice)]
        assert len(picks) == 1
        assert picks[0].level == 1

    def test_graduation_adds_advancement_dm_plus_one_note(self):
        events = [
            *_base(),
            Event(id=3, handler=PreCareerEntryHandler(precareer='Merchant Academy (Business)', roll=12)),
            Event(id=4, fulfills=(3, 0), handler=PreCareerSkillChoiceHandler(skill=Drive())),
            Event(id=5, fulfills=(3, 1), handler=PreCareerEventHandler(roll=5)),
            Event(id=6, fulfills=(3, 2), handler=PreCareerGraduationHandler(roll=9)),
        ]
        projection = replay(1, events)

        assert any('DM+1' in p for p in projection.summary.problems)

    def test_graduation_queues_career_choice_with_distinct_id(self):
        events = [
            *_base(),
            Event(id=3, handler=PreCareerEntryHandler(precareer='Merchant Academy (Business)', roll=12)),
            Event(id=4, fulfills=(3, 0), handler=PreCareerSkillChoiceHandler(skill=Drive())),
            Event(id=5, fulfills=(3, 1), handler=PreCareerEventHandler(roll=5)),
            Event(id=6, fulfills=(3, 2), handler=PreCareerGraduationHandler(roll=9)),
        ]
        projection = replay(1, events)

        career_choices = [p for p in projection.pending_inputs if isinstance(p, PendingCareerChoice)]
        assert len(career_choices) == 1
        pick_ids = {p.id for p in projection.pending_inputs if isinstance(p, PendingPreCareerSkillChoice)}
        assert career_choices[0].id not in pick_ids

    def test_honours_graduation_gives_advancement_dm_plus_two_note(self):
        events = [
            *_base(),
            Event(id=3, handler=PreCareerEntryHandler(precareer='Merchant Academy (Business)', roll=12)),
            Event(id=4, fulfills=(3, 0), handler=PreCareerSkillChoiceHandler(skill=Drive())),
            Event(id=5, fulfills=(3, 1), handler=PreCareerEventHandler(roll=5)),
            Event(id=6, fulfills=(3, 2), handler=PreCareerGraduationHandler(roll=11)),  # effective=11>=11, honours
        ]
        projection = replay(1, events)

        assert any('DM+2' in p for p in projection.summary.problems)

    def test_honours_graduation_adds_rank_two_problem_message(self):
        events = [
            *_base(),
            Event(id=3, handler=PreCareerEntryHandler(precareer='Merchant Academy (Business)', roll=12)),
            Event(id=4, fulfills=(3, 0), handler=PreCareerSkillChoiceHandler(skill=Drive())),
            Event(id=5, fulfills=(3, 1), handler=PreCareerEventHandler(roll=5)),
            Event(id=6, fulfills=(3, 2), handler=PreCareerGraduationHandler(roll=11)),
        ]
        projection = replay(1, events)

        combined = ' '.join(projection.summary.problems)
        assert 'rank 2' in combined


# ── Psionic Community ────────────────────────────────────────────────────────


class TestPsionicCommunity:
    def test_entry_auto_grants_streetwise(self):
        # 'Profession' and 'Science' are broad skill categories — they become pending picks, not auto-granted
        events = [*_base(), Event(id=3, handler=PreCareerEntryHandler(precareer='Psionic Community', roll=5))]
        projection = replay(1, events)

        assert _skill_level(projection, 'Streetwise') >= 0, 'Streetwise should be auto-granted at entry'

    def test_entry_queues_two_picks_for_profession_and_science_categories(self):
        # 'Profession' and 'Science' in skill_choices are categories; player picks a specialisation each
        events = [*_base(), Event(id=3, handler=PreCareerEntryHandler(precareer='Psionic Community', roll=5))]
        projection = replay(1, events)

        picks = [p for p in projection.pending_inputs if isinstance(p, PendingPreCareerSkillChoice)]
        assert len(picks) == 2
        # Both picks are at level 0
        assert all(p.level == 0 for p in picks)
        all_options = picks[0].options + picks[1].options
        assert any('Profession' in type(o).name() for o in all_options)
        assert any('Science' in type(o).name() for o in all_options)

    def test_entry_queues_graduation_pending_for_text_based_requirement(self):
        events = [*_base(), Event(id=3, handler=PreCareerEntryHandler(precareer='Psionic Community', roll=5))]
        projection = replay(1, events)

        assert any(isinstance(p, PendingPreCareerGraduation) for p in projection.pending_inputs)

    def test_graduation_queues_science_skill_pick_at_level_one(self):
        # Rules award Science (psionicology) 1; system queues a pick since no Psionicology exists
        # Pending IDs: '3.0'=Profession pick, '3.1'=Science pick, '3.2'=event, '3.3'=graduation
        events = [
            *_base(),
            Event(id=3, handler=PreCareerEntryHandler(precareer='Psionic Community', roll=5)),
            Event(id=4, fulfills=(3, 0), handler=PreCareerSkillChoiceHandler(skill=ColonistProfession())),
            Event(id=5, fulfills=(3, 1), handler=PreCareerSkillChoiceHandler(skill=LifeScience())),
            Event(id=6, fulfills=(3, 2), handler=PreCareerEventHandler(roll=5)),
            Event(id=7, fulfills=(3, 3), handler=PreCareerGraduationHandler(roll=10)),  # no honours (10<12)
        ]
        projection = replay(1, events)

        science_picks = [
            p for p in projection.pending_inputs if isinstance(p, PendingPreCareerSkillChoice) and p.level == 1
        ]
        assert len(science_picks) == 1
        assert any(isinstance(o, SpaceScience) for o in science_picks[0].options)

    def test_graduation_adds_rival_connection(self):
        events = [
            *_base(),
            Event(id=3, handler=PreCareerEntryHandler(precareer='Psionic Community', roll=5)),
            Event(id=4, fulfills=(3, 0), handler=PreCareerSkillChoiceHandler(skill=ColonistProfession())),
            Event(id=5, fulfills=(3, 1), handler=PreCareerSkillChoiceHandler(skill=SpaceScience())),
            Event(id=6, fulfills=(3, 2), handler=PreCareerEventHandler(roll=5)),
            Event(id=7, fulfills=(3, 3), handler=PreCareerGraduationHandler(roll=10)),
        ]
        projection = replay(1, events)

        assert any(isinstance(c, Rival) for c in projection.summary.connections)
        assert not any(isinstance(c, Enemy) for c in projection.summary.connections)

    def test_honours_graduation_adds_enemy_not_rival(self):
        events = [
            *_base(),
            Event(id=3, handler=PreCareerEntryHandler(precareer='Psionic Community', roll=5)),
            Event(id=4, fulfills=(3, 0), handler=PreCareerSkillChoiceHandler(skill=ColonistProfession())),
            Event(id=5, fulfills=(3, 1), handler=PreCareerSkillChoiceHandler(skill=SpaceScience())),
            Event(id=6, fulfills=(3, 2), handler=PreCareerEventHandler(roll=5)),
            Event(id=7, fulfills=(3, 3), handler=PreCareerGraduationHandler(roll=12)),  # honours (12>=12)
        ]
        projection = replay(1, events)

        assert any(isinstance(c, Enemy) for c in projection.summary.connections)
        assert not any(isinstance(c, Rival) for c in projection.summary.connections)

    def test_graduation_adds_psi_problem_message(self):
        events = [
            *_base(),
            Event(id=3, handler=PreCareerEntryHandler(precareer='Psionic Community', roll=5)),
            Event(id=4, fulfills=(3, 0), handler=PreCareerSkillChoiceHandler(skill=ColonistProfession())),
            Event(id=5, fulfills=(3, 1), handler=PreCareerSkillChoiceHandler(skill=SpaceScience())),
            Event(id=6, fulfills=(3, 2), handler=PreCareerEventHandler(roll=5)),
            Event(id=7, fulfills=(3, 3), handler=PreCareerGraduationHandler(roll=10)),
        ]
        projection = replay(1, events)

        assert any('PSI' in p for p in projection.summary.problems)

    def test_graduation_queues_career_choice(self):
        events = [
            *_base(),
            Event(id=3, handler=PreCareerEntryHandler(precareer='Psionic Community', roll=5)),
            Event(id=4, fulfills=(3, 0), handler=PreCareerSkillChoiceHandler(skill=ColonistProfession())),
            Event(id=5, fulfills=(3, 1), handler=PreCareerSkillChoiceHandler(skill=SpaceScience())),
            Event(id=6, fulfills=(3, 2), handler=PreCareerEventHandler(roll=5)),
            Event(id=7, fulfills=(3, 3), handler=PreCareerGraduationHandler(roll=10)),
        ]
        projection = replay(1, events)

        assert any(isinstance(p, PendingCareerChoice) for p in projection.pending_inputs)


# ── School of Hard Knocks ────────────────────────────────────────────────────


class TestSchoolOfHardKnocks:
    def test_entry_auto_grants_streetwise_at_level_one(self):
        events = [*_base(), Event(id=3, handler=PreCareerEntryHandler(precareer='School of Hard Knocks', roll=5))]
        projection = replay(1, events)

        assert _skill_level(projection, 'Streetwise') >= 1

    def test_entry_queues_two_skill_picks_at_level_zero(self):
        events = [*_base(), Event(id=3, handler=PreCareerEntryHandler(precareer='School of Hard Knocks', roll=5))]
        projection = replay(1, events)

        picks = [p for p in projection.pending_inputs if isinstance(p, PendingPreCareerSkillChoice)]
        assert len(picks) == 2
        assert all(p.level == 0 for p in picks)

    def test_entry_pick_pool_excludes_auto_granted_streetwise(self):
        events = [*_base(), Event(id=3, handler=PreCareerEntryHandler(precareer='School of Hard Knocks', roll=5))]
        projection = replay(1, events)

        picks = [p for p in projection.pending_inputs if isinstance(p, PendingPreCareerSkillChoice)]
        assert not any(isinstance(o, Streetwise) for o in picks[0].options)
        assert any(isinstance(o, Athletics) for o in picks[0].options)

    def test_graduation_grants_gun_combat(self):
        events = [
            *_base(),
            Event(id=3, handler=PreCareerEntryHandler(precareer='School of Hard Knocks', roll=5)),
            Event(id=4, fulfills=(3, 0), handler=PreCareerSkillChoiceHandler(skill=Athletics())),
            Event(id=5, fulfills=(3, 1), handler=PreCareerSkillChoiceHandler(skill=Deception())),
            Event(id=6, fulfills=(3, 2), handler=PreCareerEventHandler(roll=5)),
            Event(id=7, fulfills=(3, 3), handler=PreCareerGraduationHandler(roll=9)),  # effective=9>=7, no honours
        ]
        projection = replay(1, events)

        assert _skill_level(projection, 'Gun Combat') >= 0

    def test_graduation_decreases_soc_by_one(self):
        events = [
            *_base(),
            Event(id=3, handler=PreCareerEntryHandler(precareer='School of Hard Knocks', roll=5)),
            Event(id=4, fulfills=(3, 0), handler=PreCareerSkillChoiceHandler(skill=Athletics())),
            Event(id=5, fulfills=(3, 1), handler=PreCareerSkillChoiceHandler(skill=Deception())),
            Event(id=6, fulfills=(3, 2), handler=PreCareerEventHandler(roll=5)),
            Event(id=7, fulfills=(3, 3), handler=PreCareerGraduationHandler(roll=9)),
        ]
        projection = replay(1, events)

        assert projection.summary.characteristics[Chars.SOC] == 6  # 7-1

    def test_graduation_queues_three_skill_picks_at_level_zero(self):
        events = [
            *_base(),
            Event(id=3, handler=PreCareerEntryHandler(precareer='School of Hard Knocks', roll=5)),
            Event(id=4, fulfills=(3, 0), handler=PreCareerSkillChoiceHandler(skill=Athletics())),
            Event(id=5, fulfills=(3, 1), handler=PreCareerSkillChoiceHandler(skill=Deception())),
            Event(id=6, fulfills=(3, 2), handler=PreCareerEventHandler(roll=5)),
            Event(id=7, fulfills=(3, 3), handler=PreCareerGraduationHandler(roll=9)),
        ]
        projection = replay(1, events)

        picks = [p for p in projection.pending_inputs if isinstance(p, PendingPreCareerSkillChoice)]
        assert len(picks) == 3
        assert all(p.level == 0 for p in picks)

    def test_graduation_queues_career_choice_with_distinct_id(self):
        events = [
            *_base(),
            Event(id=3, handler=PreCareerEntryHandler(precareer='School of Hard Knocks', roll=5)),
            Event(id=4, fulfills=(3, 0), handler=PreCareerSkillChoiceHandler(skill=Athletics())),
            Event(id=5, fulfills=(3, 1), handler=PreCareerSkillChoiceHandler(skill=Deception())),
            Event(id=6, fulfills=(3, 2), handler=PreCareerEventHandler(roll=5)),
            Event(id=7, fulfills=(3, 3), handler=PreCareerGraduationHandler(roll=9)),
        ]
        projection = replay(1, events)

        career_choices = [p for p in projection.pending_inputs if isinstance(p, PendingCareerChoice)]
        assert len(career_choices) == 1
        pick_ids = {p.id for p in projection.pending_inputs if isinstance(p, PendingPreCareerSkillChoice)}
        assert career_choices[0].id not in pick_ids

    def test_graduation_adds_dm_minus_two_problem(self):
        events = [
            *_base(),
            Event(id=3, handler=PreCareerEntryHandler(precareer='School of Hard Knocks', roll=5)),
            Event(id=4, fulfills=(3, 0), handler=PreCareerSkillChoiceHandler(skill=Athletics())),
            Event(id=5, fulfills=(3, 1), handler=PreCareerSkillChoiceHandler(skill=Deception())),
            Event(id=6, fulfills=(3, 2), handler=PreCareerEventHandler(roll=5)),
            Event(id=7, fulfills=(3, 3), handler=PreCareerGraduationHandler(roll=9)),
        ]
        projection = replay(1, events)

        assert any('DM-2' in p for p in projection.summary.problems)

    def test_honours_graduation_grants_carouse_at_level_one(self):
        events = [
            *_base(),
            Event(id=3, handler=PreCareerEntryHandler(precareer='School of Hard Knocks', roll=5)),
            Event(id=4, fulfills=(3, 0), handler=PreCareerSkillChoiceHandler(skill=Athletics())),
            Event(id=5, fulfills=(3, 1), handler=PreCareerSkillChoiceHandler(skill=Deception())),
            Event(id=6, fulfills=(3, 2), handler=PreCareerEventHandler(roll=5)),
            Event(id=7, fulfills=(3, 3), handler=PreCareerGraduationHandler(roll=11)),  # effective=11>=11, honours
        ]
        projection = replay(1, events)

        assert _skill_level(projection, 'Carouse') >= 1

    def test_honours_graduation_queues_four_picks_including_one_at_level_one(self):
        events = [
            *_base(),
            Event(id=3, handler=PreCareerEntryHandler(precareer='School of Hard Knocks', roll=5)),
            Event(id=4, fulfills=(3, 0), handler=PreCareerSkillChoiceHandler(skill=Athletics())),
            Event(id=5, fulfills=(3, 1), handler=PreCareerSkillChoiceHandler(skill=Deception())),
            Event(id=6, fulfills=(3, 2), handler=PreCareerEventHandler(roll=5)),
            Event(id=7, fulfills=(3, 3), handler=PreCareerGraduationHandler(roll=11)),
        ]
        projection = replay(1, events)

        picks = [p for p in projection.pending_inputs if isinstance(p, PendingPreCareerSkillChoice)]
        assert len(picks) == 4
        assert sum(1 for p in picks if p.level == 1) == 1

    def test_honours_career_choice_id_distinct_from_four_picks(self):
        events = [
            *_base(),
            Event(id=3, handler=PreCareerEntryHandler(precareer='School of Hard Knocks', roll=5)),
            Event(id=4, fulfills=(3, 0), handler=PreCareerSkillChoiceHandler(skill=Athletics())),
            Event(id=5, fulfills=(3, 1), handler=PreCareerSkillChoiceHandler(skill=Deception())),
            Event(id=6, fulfills=(3, 2), handler=PreCareerEventHandler(roll=5)),
            Event(id=7, fulfills=(3, 3), handler=PreCareerGraduationHandler(roll=11)),
        ]
        projection = replay(1, events)

        career_choices = [p for p in projection.pending_inputs if isinstance(p, PendingCareerChoice)]
        pick_ids = {p.id for p in projection.pending_inputs if isinstance(p, PendingPreCareerSkillChoice)}
        assert len(career_choices) == 1
        assert career_choices[0].id not in pick_ids


# ── Spacer Community ─────────────────────────────────────────────────────────


class TestSpacerCommunity:
    def test_entry_auto_grants_vacc_suit_at_level_one(self):
        events = [*_base(), Event(id=3, handler=PreCareerEntryHandler(precareer='Spacer Community', roll=5))]
        projection = replay(1, events)

        assert _skill_level(projection, 'Vacc Suit') >= 1

    def test_entry_queues_two_skill_picks_at_level_zero(self):
        events = [*_base(), Event(id=3, handler=PreCareerEntryHandler(precareer='Spacer Community', roll=5))]
        projection = replay(1, events)

        picks = [p for p in projection.pending_inputs if isinstance(p, PendingPreCareerSkillChoice)]
        assert len(picks) == 2
        assert all(p.level == 0 for p in picks)

    def test_entry_pick_pool_excludes_auto_granted_vacc_suit(self):
        events = [*_base(), Event(id=3, handler=PreCareerEntryHandler(precareer='Spacer Community', roll=5))]
        projection = replay(1, events)

        picks = [p for p in projection.pending_inputs if isinstance(p, PendingPreCareerSkillChoice)]
        assert not any(type(o).name() == 'Vacc Suit' for o in picks[0].options)
        assert any(isinstance(o, Astrogation) for o in picks[0].options)

    def test_graduation_grants_pilot(self):
        # DEX=7 (>=6) → graduation_dms DEX_6+ applies: effective = roll + DM(INT=7) + 1 = roll+1
        events = [
            *_base(),
            Event(id=3, handler=PreCareerEntryHandler(precareer='Spacer Community', roll=5)),
            Event(id=4, fulfills=(3, 0), handler=PreCareerSkillChoiceHandler(skill=Astrogation())),
            Event(id=5, fulfills=(3, 1), handler=PreCareerSkillChoiceHandler(skill=Electronics())),
            Event(id=6, fulfills=(3, 2), handler=PreCareerEventHandler(roll=5)),
            Event(id=7, fulfills=(3, 3), handler=PreCareerGraduationHandler(roll=9)),  # effective=10>=8, no honours
        ]
        projection = replay(1, events)

        assert _skill_level(projection, 'Pilot') >= 0

    def test_graduation_increases_dex_by_one(self):
        events = [
            *_base(),
            Event(id=3, handler=PreCareerEntryHandler(precareer='Spacer Community', roll=5)),
            Event(id=4, fulfills=(3, 0), handler=PreCareerSkillChoiceHandler(skill=Astrogation())),
            Event(id=5, fulfills=(3, 1), handler=PreCareerSkillChoiceHandler(skill=Electronics())),
            Event(id=6, fulfills=(3, 2), handler=PreCareerEventHandler(roll=5)),
            Event(id=7, fulfills=(3, 3), handler=PreCareerGraduationHandler(roll=9)),
        ]
        projection = replay(1, events)

        assert projection.summary.characteristics[Chars.DEX] == 8  # 7+1

    def test_graduation_decreases_soc_by_two(self):
        events = [
            *_base(),
            Event(id=3, handler=PreCareerEntryHandler(precareer='Spacer Community', roll=5)),
            Event(id=4, fulfills=(3, 0), handler=PreCareerSkillChoiceHandler(skill=Astrogation())),
            Event(id=5, fulfills=(3, 1), handler=PreCareerSkillChoiceHandler(skill=Electronics())),
            Event(id=6, fulfills=(3, 2), handler=PreCareerEventHandler(roll=5)),
            Event(id=7, fulfills=(3, 3), handler=PreCareerGraduationHandler(roll=9)),
        ]
        projection = replay(1, events)

        assert projection.summary.characteristics[Chars.SOC] == 5  # 7-2

    def test_graduation_queues_two_level_zero_and_one_level_one_pick(self):
        events = [
            *_base(),
            Event(id=3, handler=PreCareerEntryHandler(precareer='Spacer Community', roll=5)),
            Event(id=4, fulfills=(3, 0), handler=PreCareerSkillChoiceHandler(skill=Astrogation())),
            Event(id=5, fulfills=(3, 1), handler=PreCareerSkillChoiceHandler(skill=Electronics())),
            Event(id=6, fulfills=(3, 2), handler=PreCareerEventHandler(roll=5)),
            Event(id=7, fulfills=(3, 3), handler=PreCareerGraduationHandler(roll=9)),
        ]
        projection = replay(1, events)

        picks = [p for p in projection.pending_inputs if isinstance(p, PendingPreCareerSkillChoice)]
        assert len(picks) == 3
        assert sum(1 for p in picks if p.level == 0) == 2
        assert sum(1 for p in picks if p.level == 1) == 1

    def test_graduation_adds_qualification_dm(self):
        events = [
            *_base(),
            Event(id=3, handler=PreCareerEntryHandler(precareer='Spacer Community', roll=5)),
            Event(id=4, fulfills=(3, 0), handler=PreCareerSkillChoiceHandler(skill=Astrogation())),
            Event(id=5, fulfills=(3, 1), handler=PreCareerSkillChoiceHandler(skill=Electronics())),
            Event(id=6, fulfills=(3, 2), handler=PreCareerEventHandler(roll=5)),
            Event(id=7, fulfills=(3, 3), handler=PreCareerGraduationHandler(roll=9)),
        ]
        projection = replay(1, events)

        assert projection.pending_qualification_dm == 1

    def test_graduation_queues_career_choice_with_distinct_id(self):
        events = [
            *_base(),
            Event(id=3, handler=PreCareerEntryHandler(precareer='Spacer Community', roll=5)),
            Event(id=4, fulfills=(3, 0), handler=PreCareerSkillChoiceHandler(skill=Astrogation())),
            Event(id=5, fulfills=(3, 1), handler=PreCareerSkillChoiceHandler(skill=Electronics())),
            Event(id=6, fulfills=(3, 2), handler=PreCareerEventHandler(roll=5)),
            Event(id=7, fulfills=(3, 3), handler=PreCareerGraduationHandler(roll=9)),
        ]
        projection = replay(1, events)

        career_choices = [p for p in projection.pending_inputs if isinstance(p, PendingCareerChoice)]
        assert len(career_choices) == 1
        pick_ids = {p.id for p in projection.pending_inputs if isinstance(p, PendingPreCareerSkillChoice)}
        assert career_choices[0].id not in pick_ids

    def test_honours_graduation_grants_jack_of_all_trades(self):
        events = [
            *_base(),
            Event(id=3, handler=PreCareerEntryHandler(precareer='Spacer Community', roll=5)),
            Event(id=4, fulfills=(3, 0), handler=PreCareerSkillChoiceHandler(skill=Astrogation())),
            Event(id=5, fulfills=(3, 1), handler=PreCareerSkillChoiceHandler(skill=Electronics())),
            Event(id=6, fulfills=(3, 2), handler=PreCareerEventHandler(roll=5)),
            Event(id=7, fulfills=(3, 3), handler=PreCareerGraduationHandler(roll=11)),  # effective=12>=12, honours
        ]
        projection = replay(1, events)

        assert _skill_level(projection, 'Jack-of-All-Trades') >= 1


class TestUniversity:
    # _base() uses EDU=0 (no background skills). University requires EDU 6+; with EDU=0 (DM-3),
    # a roll of 9 yields effective 6, which just passes. All tests use roll=9 for entry.

    def test_entry_queues_level_zero_and_level_one_skill_picks(self):
        events = [*_base(), Event(id=3, handler=PreCareerEntryHandler(precareer='University', roll=9))]
        projection = replay(1, events)

        picks = [p for p in projection.pending_inputs if isinstance(p, PendingPreCareerSkillChoice)]
        assert sum(1 for p in picks if p.level == 0) == 1
        assert sum(1 for p in picks if p.level == 1) == 1

    def test_level_one_options_contain_specialisation_labels_not_base_names(self):
        events = [*_base(), Event(id=3, handler=PreCareerEntryHandler(precareer='University', roll=9))]
        projection = replay(1, events)

        level1_picks = [
            p for p in projection.pending_inputs if isinstance(p, PendingPreCareerSkillChoice) and p.level == 1
        ]
        assert len(level1_picks) == 1
        # Check what the user actually sees: _expanded_options() handles specialisation expansion
        opts = level1_picks[0]._expanded_options()
        ps_opts = [o for o in opts if isinstance(o, PhysicalScience)]
        assert not any(
            all(getattr(o, f).value == 0 for f in ('chemistry', 'physics', 'jumpspace_physics')) for o in ps_opts
        ), 'bare Physical Science without active spec must not appear at level 1'
        assert any(o.chemistry.value > 0 for o in ps_opts)
        assert any(o.physics.value > 0 for o in ps_opts)
        assert any(o.jumpspace_physics.value > 0 for o in ps_opts)

    def test_level_zero_options_contain_base_skill_names(self):
        events = [*_base(), Event(id=3, handler=PreCareerEntryHandler(precareer='University', roll=9))]
        projection = replay(1, events)

        level0_picks = [
            p for p in projection.pending_inputs if isinstance(p, PendingPreCareerSkillChoice) and p.level == 0
        ]
        assert len(level0_picks) == 1
        opts = level0_picks[0].options
        assert any(isinstance(o, PhysicalScience) for o in opts), 'Physical Science must appear at level 0'
        # Level-0 options are base instances with no active spec
        assert not any(isinstance(o, PhysicalScience) and o.chemistry.value > 0 for o in opts), (
            'Physical Science (Chemistry) must not appear at level 0'
        )

    def test_choosing_specialised_skill_at_level_one_grants_only_that_spec(self):
        # Selecting 'Physical Science (Chemistry)' at level 1 must not grant all Physical Science specs.
        events = [
            *_base(),
            Event(id=3, handler=PreCareerEntryHandler(precareer='University', roll=9)),
            Event(id=4, fulfills=(3, 0), handler=PreCareerSkillChoiceHandler(skill=Admin())),
            Event(
                id=5,
                fulfills=(3, 1),
                handler=PreCareerSkillChoiceHandler(skill=PhysicalScience(chemistry=Level(value=1))),
            ),
        ]
        projection = replay(1, events)

        ps_skill = next((s for s in projection.summary.skills if type(s).name() == 'Physical Science'), None)
        assert ps_skill is not None
        assert isinstance(ps_skill, PhysicalScience)
        assert ps_skill.chemistry.value == 1
        assert ps_skill.physics.value == 0
        assert ps_skill.jumpspace_physics.value == 0

    def test_graduation_increments_chosen_specialisation_not_all(self):
        # After graduation, Physical Science (Chemistry) 1 should become Chemistry 2, not all specs 2.
        events = [
            *_base(),
            Event(id=3, handler=PreCareerEntryHandler(precareer='University', roll=9)),
            Event(id=4, fulfills=(3, 0), handler=PreCareerSkillChoiceHandler(skill=Admin())),
            Event(
                id=5,
                fulfills=(3, 1),
                handler=PreCareerSkillChoiceHandler(skill=PhysicalScience(chemistry=Level(value=1))),
            ),
            Event(id=6, fulfills=(3, 2), handler=PreCareerEventHandler(roll=5)),
            Event(id=7, fulfills=(3, 3), handler=PreCareerGraduationHandler(roll=8)),  # INT=7, DM+0, effective=8 >= 6
        ]
        projection = replay(1, events)

        ps_skill = next((s for s in projection.summary.skills if type(s).name() == 'Physical Science'), None)
        assert ps_skill is not None
        assert isinstance(ps_skill, PhysicalScience)
        assert ps_skill.chemistry.value == 2
        assert ps_skill.physics.value == 0
        assert ps_skill.jumpspace_physics.value == 0
