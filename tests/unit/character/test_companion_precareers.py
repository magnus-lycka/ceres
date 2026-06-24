"""Tests for precareer entry and graduation (core University and Mongoose Traveller Companion precareers)."""

from typing import Literal

from ceres.character.domain.career.career_data import CharCheck
from ceres.character.domain.career.career_events import PendingCareerChoice
from ceres.character.domain.character_start import CharacterStartedHandler, UcpHandler
from ceres.character.domain.characteristics import Chars
from ceres.character.domain.connection import Enemy, Rival
from ceres.character.domain.precareer.colonial_upbringing import ColonialUprbringingPreCareer
from ceres.character.domain.precareer.loader import precareer_of_type
from ceres.character.domain.precareer.merchant_academy import (
    MerchantAcademyBusinessPreCareer,
    MerchantAcademyShipboardPreCareer,
)
from ceres.character.domain.precareer.precareer_data import PreCareerData
from ceres.character.domain.precareer.precareer_events import (
    PendingPreCareerEvent,
    PendingPreCareerGraduation,
    PendingPreCareerSkillChoice,
    PreCareerEntryHandler,
    PreCareerEventHandler,
    PreCareerGraduationHandler,
    PreCareerSkillChoiceHandler,
)
from ceres.character.domain.precareer.psionic_community import PsionicCommunityPreCareer
from ceres.character.domain.precareer.school_of_hard_knocks import SchoolOfHardKnocksPreCareer
from ceres.character.domain.precareer.spacer_community import SpacerCommunityPreCareer
from ceres.character.domain.precareer.university import UniversityPreCareer
from ceres.character.domain.psionics import (
    Clairvoyance,
    PendingPsionicTalentLevelChoice,
    Psionics,
    PsionicTalentLevelHandler,
    Telepathy,
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
    level_fields,
)
from ceres.character.domain.sophont import HUMANITI
from ceres.character.mechanism.event_base import Event, EventHandlerBase
from ceres.character.mechanism.replay import replay
from tests.unit.character.helpers import MOCK_WORLD, pending_id as _pending, scripted_event as _event


def _base():
    """Character with EDU=0 (no background skills) and all other stats at 7."""
    started = _event(
        handler=CharacterStartedHandler(sophont=HUMANITI, homeworld=MOCK_WORLD, player='Test', name='Tester')
    )
    ucp = _event(
        fulfills=_pending(started, 0),
        handler=UcpHandler(ucp='777707'),  # STR=7 DEX=7 END=7 INT=7 EDU=0 SOC=7
    )
    return [started, ucp]


class _EstablishPsiForTest(EventHandlerBase):
    kind: Literal['test_establish_psi_for_precareer'] = 'test_establish_psi_for_precareer'

    def apply(self, projection, event, fulfilled_pending=None) -> None:
        projection.summary.characteristics[Chars.PSI] = 9
        projection.summary.psionics = Psionics(talent_acquisition_checks=1)


def _psionic_base():
    return [*_base(), Event(handler=_EstablishPsiForTest())]


class _EstablishTrainedPsiForTest(EventHandlerBase):
    kind: Literal['test_establish_trained_psi_for_precareer'] = 'test_establish_trained_psi_for_precareer'

    def apply(self, projection, event, fulfilled_pending=None) -> None:
        projection.summary.characteristics[Chars.PSI] = 9
        projection.summary.psionics = Psionics(
            psionic_talent_skills=[Telepathy(), Clairvoyance()],
            talent_acquisition_checks=5,
        )


def _trained_psionic_base():
    return [*_base(), Event(handler=_EstablishTrainedPsiForTest())]


def _skill_level(projection, name: str) -> int:
    """Highest level of a named skill in the projection, or -1 if absent."""
    skill = next((s for s in projection.summary.skills if type(s).name() == name), None)
    if skill is None:
        return -1
    fields = level_fields(type(skill))
    return max((getattr(skill, f).value for f in fields), default=0)


def _precareer_entry_events(
    precareer_type: type[PreCareerData],
    roll: int,
    base_events: list[Event] | None = None,
) -> list[Event]:
    precareer = precareer_of_type(precareer_type)
    return [
        *(base_events or _base()),
        _event(handler=PreCareerEntryHandler(precareer=precareer, roll=roll)),
    ]


def _precareer_graduation_events(
    precareer_type: type[PreCareerData],
    *,
    entry_roll: int,
    skills: list,
    event_roll: int = 5,
    graduation_roll: int,
    base_events: list[Event] | None = None,
) -> list[Event]:
    events = _precareer_entry_events(precareer_type, entry_roll, base_events)
    entry = events[-1]
    for index, skill in enumerate(skills):
        events.append(_event(fulfills=_pending(entry, index), handler=PreCareerSkillChoiceHandler(skill=skill)))
    events.append(_event(fulfills=_pending(entry, len(skills)), handler=PreCareerEventHandler(roll=event_roll)))
    events.append(
        _event(
            fulfills=_pending(entry, len(skills) + 1),
            handler=PreCareerGraduationHandler(roll=graduation_roll),
        )
    )
    return events


# ── Colonial Upbringing ───────────────────────────────────────────────────────


def _colonial_entry_events() -> list[Event]:
    return _precareer_entry_events(ColonialUprbringingPreCareer, 5)


def _colonial_graduation_events(graduation_roll: int = 10) -> list[Event]:
    return _precareer_graduation_events(
        ColonialUprbringingPreCareer,
        entry_roll=5,
        skills=[ColonistProfession()],
        graduation_roll=graduation_roll,
    )


class TestColonialUpbringing:
    def test_entry_auto_grants_nine_concrete_level_zero_skills(self):
        # 'Profession' is a broad skill category — it becomes a pending pick, not auto-granted
        projection = replay(1, _colonial_entry_events())

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
        projection = replay(1, _colonial_entry_events())

        assert _skill_level(projection, 'Survival') >= 1

    def test_entry_queues_one_skill_pick_for_profession_category(self):
        # 'Profession' in the Colonial skill list is a category; player must pick a specialisation
        projection = replay(1, _colonial_entry_events())

        picks = [p for p in projection.pending_inputs if isinstance(p, PendingPreCareerSkillChoice)]
        assert len(picks) == 1
        assert picks[0].level == 0
        assert any(isinstance(o, ColonistProfession) for o in picks[0].options)

    def test_entry_queues_event_and_graduation_pendings(self):
        projection = replay(1, _colonial_entry_events())

        assert any(isinstance(p, PendingPreCareerEvent) for p in projection.pending_inputs)
        assert any(isinstance(p, PendingPreCareerGraduation) for p in projection.pending_inputs)

    def test_graduation_grants_jack_of_all_trades_at_level_one(self):
        projection = replay(1, _colonial_graduation_events())

        assert _skill_level(projection, 'Jack-of-All-Trades') >= 1

    def test_graduation_increases_end_by_one(self):
        projection = replay(1, _colonial_graduation_events())

        assert projection.summary.characteristics[Chars.END] == 8  # 7+1

    def test_graduation_queues_three_skill_picks_at_level_one(self):
        projection = replay(1, _colonial_graduation_events())

        picks = [p for p in projection.pending_inputs if isinstance(p, PendingPreCareerSkillChoice)]
        assert len(picks) == 3
        assert all(p.level == 1 for p in picks)

    def test_graduation_queues_career_choice_with_distinct_id(self):
        projection = replay(1, _colonial_graduation_events())

        career_choices = [p for p in projection.pending_inputs if isinstance(p, PendingCareerChoice)]
        assert len(career_choices) == 1
        pick_ids = {p.id for p in projection.pending_inputs if isinstance(p, PendingPreCareerSkillChoice)}
        assert career_choices[0].id not in pick_ids

    def test_graduation_adds_edu_and_age_problem_messages(self):
        projection = replay(1, _colonial_graduation_events())

        combined = ' '.join(projection.summary.problems)
        assert 'EDU' in combined
        assert 'age' in combined.lower()

    def test_honours_graduation_grants_leadership_and_extra_pick(self):
        projection = replay(1, _colonial_graduation_events(graduation_roll=12))

        assert _skill_level(projection, 'Leadership') >= 1
        picks = [p for p in projection.pending_inputs if isinstance(p, PendingPreCareerSkillChoice)]
        assert len(picks) == 4  # 3 regular + 1 honours

    def test_graduation_pick_options_expand_specialized_skills_to_specs(self):
        # Gun Combat is a specialized skill — at level 1, the player must choose a spec,
        # so the option should appear as 'Gun Combat (Archaic)' etc., not bare 'Gun Combat'.
        events = _colonial_graduation_events()
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
            *(base := _colonial_graduation_events()),
            _event(
                fulfills=_pending(base[-1], 0),
                handler=PreCareerSkillChoiceHandler(skill=GunCombat(slug=Level(value=1))),
            ),
        ]
        projection = replay(1, events)
        gc = next((s for s in projection.summary.skills if isinstance(s, GunCombat)), None)
        assert gc is not None
        assert gc.slug.value == 1
        assert gc.energy.value == 0
        assert gc.archaic.value == 0

    def test_honours_career_choice_id_distinct_from_four_picks(self):
        projection = replay(1, _colonial_graduation_events(graduation_roll=12))

        career_choices = [p for p in projection.pending_inputs if isinstance(p, PendingCareerChoice)]
        pick_ids = {p.id for p in projection.pending_inputs if isinstance(p, PendingPreCareerSkillChoice)}
        assert len(career_choices) == 1
        assert career_choices[0].id not in pick_ids


# ── Merchant Academy ─────────────────────────────────────────────────────────


class TestMerchantAcademy:
    def test_entry_business_grants_broker_table_skills_at_level_zero(self):
        events = _precareer_entry_events(MerchantAcademyBusinessPreCareer, 12)
        projection = replay(1, events)

        for name in ('Admin', 'Advocate', 'Broker', 'Streetwise', 'Deception', 'Persuade'):
            assert _skill_level(projection, name) >= 0, f'{name} should be granted at level 0'

    def test_entry_shipboard_grants_merchant_marine_skills_at_level_zero(self):
        events = _precareer_entry_events(MerchantAcademyShipboardPreCareer, 12)
        projection = replay(1, events)

        for name in ('Pilot', 'Vacc Suit', 'Athletics', 'Mechanic', 'Engineer', 'Electronics'):
            assert _skill_level(projection, name) >= 0, f'{name} should be granted at level 0'

    def test_entry_queues_one_service_skill_pick_at_level_one(self):
        events = _precareer_entry_events(MerchantAcademyBusinessPreCareer, 12)
        projection = replay(1, events)

        picks = [p for p in projection.pending_inputs if isinstance(p, PendingPreCareerSkillChoice)]
        assert len(picks) == 1
        assert picks[0].level == 1

    def test_entry_service_skill_options_are_merchant_service_skills(self):
        events = _precareer_entry_events(MerchantAcademyBusinessPreCareer, 12)
        projection = replay(1, events)

        picks = [p for p in projection.pending_inputs if isinstance(p, PendingPreCareerSkillChoice)]
        assert any(isinstance(o, Drive) for o in picks[0].options)

    def test_shipboard_entry_grants_pilot_not_broker_skills(self):
        events = _precareer_entry_events(MerchantAcademyShipboardPreCareer, 12)
        projection = replay(1, events)

        assert _skill_level(projection, 'Pilot') >= 0
        assert _skill_level(projection, 'Broker') == -1

    def test_graduation_increases_edu_by_one(self):
        events = _precareer_graduation_events(
            MerchantAcademyBusinessPreCareer, entry_roll=12, skills=[Drive()], graduation_roll=9
        )
        projection = replay(1, events)

        assert projection.summary.characteristics[Chars.EDU] == 1  # 0+1

    def test_graduation_queues_one_curriculum_skill_pick_at_level_one(self):
        events = _precareer_graduation_events(
            MerchantAcademyBusinessPreCareer, entry_roll=12, skills=[Drive()], graduation_roll=9
        )
        projection = replay(1, events)

        picks = [p for p in projection.pending_inputs if isinstance(p, PendingPreCareerSkillChoice)]
        assert len(picks) == 1
        assert picks[0].level == 1

    def test_graduation_adds_advancement_dm_plus_one_note(self):
        events = _precareer_graduation_events(
            MerchantAcademyBusinessPreCareer, entry_roll=12, skills=[Drive()], graduation_roll=9
        )
        projection = replay(1, events)

        assert any('DM+1' in p for p in projection.summary.problems)

    def test_graduation_queues_career_choice_with_distinct_id(self):
        events = _precareer_graduation_events(
            MerchantAcademyBusinessPreCareer, entry_roll=12, skills=[Drive()], graduation_roll=9
        )
        projection = replay(1, events)

        career_choices = [p for p in projection.pending_inputs if isinstance(p, PendingCareerChoice)]
        assert len(career_choices) == 1
        pick_ids = {p.id for p in projection.pending_inputs if isinstance(p, PendingPreCareerSkillChoice)}
        assert career_choices[0].id not in pick_ids

    def test_honours_graduation_gives_advancement_dm_plus_two_note(self):
        events = _precareer_graduation_events(
            MerchantAcademyBusinessPreCareer, entry_roll=12, skills=[Drive()], graduation_roll=11
        )
        projection = replay(1, events)

        assert any('DM+2' in p for p in projection.summary.problems)

    def test_honours_graduation_adds_rank_two_problem_message(self):
        events = _precareer_graduation_events(
            MerchantAcademyBusinessPreCareer, entry_roll=12, skills=[Drive()], graduation_roll=11
        )
        projection = replay(1, events)

        combined = ' '.join(projection.summary.problems)
        assert 'rank 2' in combined


# ── Psionic Community ────────────────────────────────────────────────────────


class TestPsionicCommunity:
    def test_entry_and_graduation_use_psi_checks_with_int_bonus(self):
        precareer = precareer_of_type(PsionicCommunityPreCareer)

        assert precareer.entry == CharCheck(characteristic=Chars.PSI, target=8)
        assert precareer.entry_dms == {'INT_8+': 1}
        assert precareer.graduation == CharCheck(characteristic=Chars.PSI, target=6)
        assert precareer.graduation_dms == {'INT_8+': 1}

    def test_failed_entry_returns_to_career_choice(self):
        events = _precareer_entry_events(PsionicCommunityPreCareer, 2, _psionic_base())

        projection = replay(1, events)

        assert projection.summary.precareer is None
        assert any(isinstance(p, PendingCareerChoice) for p in projection.pending_inputs)

    def test_entry_auto_grants_streetwise(self):
        # 'Profession' and 'Science' are broad skill categories — they become pending picks, not auto-granted
        events = _precareer_entry_events(PsionicCommunityPreCareer, 7, _psionic_base())
        projection = replay(1, events)

        assert _skill_level(projection, 'Streetwise') >= 0, 'Streetwise should be auto-granted at entry'

    def test_entry_queues_two_picks_for_profession_and_science_categories(self):
        # 'Profession' and 'Science' in skill_choices are categories; player picks a specialisation each
        events = _precareer_entry_events(PsionicCommunityPreCareer, 7, _psionic_base())
        projection = replay(1, events)

        picks = [p for p in projection.pending_inputs if isinstance(p, PendingPreCareerSkillChoice)]
        assert len(picks) == 2
        # Both picks are at level 0
        assert all(p.level == 0 for p in picks)
        all_options = picks[0].options + picks[1].options
        assert any('Profession' in type(o).name() for o in all_options)
        assert any('Science' in type(o).name() for o in all_options)

    def test_entry_queues_graduation_pending(self):
        events = _precareer_entry_events(PsionicCommunityPreCareer, 7, _psionic_base())
        projection = replay(1, events)

        assert any(isinstance(p, PendingPreCareerGraduation) for p in projection.pending_inputs)

    def test_failed_graduation_does_not_grant_graduation_benefits(self):
        events = _precareer_graduation_events(
            PsionicCommunityPreCareer,
            entry_roll=7,
            skills=[ColonistProfession(), LifeScience()],
            graduation_roll=2,
            base_events=_trained_psionic_base(),
        )

        projection = replay(1, events)

        assert projection.summary.characteristics[Chars.PSI] == 9
        life_science = next(skill for skill in projection.summary.skills if isinstance(skill, LifeScience))
        assert life_science.psionicology.value == 0
        assert not any(isinstance(p, PendingPsionicTalentLevelChoice) for p in projection.pending_inputs)
        assert 'Did not graduate from Psionic Community.' in projection.summary.narrative

    def test_graduation_grants_psionicology_and_queues_possessed_talent_at_level_one(self):
        events = _precareer_graduation_events(
            PsionicCommunityPreCareer,
            entry_roll=7,
            skills=[ColonistProfession(), LifeScience()],
            graduation_roll=10,
            base_events=_trained_psionic_base(),
        )
        projection = replay(1, events)

        life_science = next(skill for skill in projection.summary.skills if isinstance(skill, LifeScience))
        assert life_science.psionicology.value == 1
        talent_pick = next(p for p in projection.pending_inputs if isinstance(p, PendingPsionicTalentLevelChoice))
        assert talent_pick.level == 1

    def test_honours_graduation_raises_all_talents_to_one_and_offers_one_at_level_two(self):
        events = _precareer_graduation_events(
            PsionicCommunityPreCareer,
            entry_roll=7,
            skills=[ColonistProfession(), LifeScience()],
            graduation_roll=12,
            base_events=_trained_psionic_base(),
        )

        projection = replay(1, events)

        assert projection.summary.psionics is not None
        assert projection.summary.psionics.talent_level(Telepathy) == 1
        assert projection.summary.psionics.talent_level(Clairvoyance) == 1
        talent_pick = next(p for p in projection.pending_inputs if isinstance(p, PendingPsionicTalentLevelChoice))
        assert talent_pick.level == 2

        events.append(
            _event(
                fulfills=talent_pick.pending_id,
                handler=PsionicTalentLevelHandler(talent=Telepathy(), level=2),
            )
        )
        projection = replay(1, events)

        assert projection.summary.psionics is not None
        assert projection.summary.psionics.talent_level(Telepathy) == 2

    def test_graduation_adds_rival_connection(self):
        events = _precareer_graduation_events(
            PsionicCommunityPreCareer,
            entry_roll=7,
            skills=[ColonistProfession(), SpaceScience()],
            graduation_roll=10,
            base_events=_psionic_base(),
        )
        projection = replay(1, events)

        assert any(isinstance(c, Rival) for c in projection.summary.connections)
        assert not any(isinstance(c, Enemy) for c in projection.summary.connections)

    def test_honours_graduation_adds_enemy_not_rival(self):
        events = _precareer_graduation_events(
            PsionicCommunityPreCareer,
            entry_roll=7,
            skills=[ColonistProfession(), SpaceScience()],
            graduation_roll=12,
            base_events=_psionic_base(),
        )
        projection = replay(1, events)

        assert any(isinstance(c, Enemy) for c in projection.summary.connections)
        assert not any(isinstance(c, Rival) for c in projection.summary.connections)

    def test_graduation_increases_psi_and_auto_qualifies_for_psion(self):
        events = _precareer_graduation_events(
            PsionicCommunityPreCareer,
            entry_roll=7,
            skills=[ColonistProfession(), SpaceScience()],
            graduation_roll=10,
            base_events=_psionic_base(),
        )
        projection = replay(1, events)

        assert projection.summary.characteristics[Chars.PSI] == 10
        from ceres.character.domain.career.psion import Psion

        assert Psion in projection.auto_qualify_careers

    def test_graduation_queues_career_choice(self):
        events = _precareer_graduation_events(
            PsionicCommunityPreCareer,
            entry_roll=7,
            skills=[ColonistProfession(), SpaceScience()],
            graduation_roll=10,
            base_events=_psionic_base(),
        )
        projection = replay(1, events)

        assert any(isinstance(p, PendingCareerChoice) for p in projection.pending_inputs)


# ── School of Hard Knocks ────────────────────────────────────────────────────


class TestSchoolOfHardKnocks:
    def test_entry_auto_grants_streetwise_at_level_one(self):
        events = _precareer_entry_events(SchoolOfHardKnocksPreCareer, 5)
        projection = replay(1, events)

        assert _skill_level(projection, 'Streetwise') >= 1

    def test_entry_queues_two_skill_picks_at_level_zero(self):
        events = _precareer_entry_events(SchoolOfHardKnocksPreCareer, 5)
        projection = replay(1, events)

        picks = [p for p in projection.pending_inputs if isinstance(p, PendingPreCareerSkillChoice)]
        assert len(picks) == 2
        assert all(p.level == 0 for p in picks)

    def test_entry_pick_pool_excludes_auto_granted_streetwise(self):
        events = _precareer_entry_events(SchoolOfHardKnocksPreCareer, 5)
        projection = replay(1, events)

        picks = [p for p in projection.pending_inputs if isinstance(p, PendingPreCareerSkillChoice)]
        assert not any(isinstance(o, Streetwise) for o in picks[0].options)
        assert any(isinstance(o, Athletics) for o in picks[0].options)

    def test_graduation_grants_gun_combat(self):
        events = _precareer_graduation_events(
            SchoolOfHardKnocksPreCareer, entry_roll=5, skills=[Athletics(), Deception()], graduation_roll=9
        )
        projection = replay(1, events)

        assert _skill_level(projection, 'Gun Combat') >= 0

    def test_graduation_decreases_soc_by_one(self):
        events = _precareer_graduation_events(
            SchoolOfHardKnocksPreCareer, entry_roll=5, skills=[Athletics(), Deception()], graduation_roll=9
        )
        projection = replay(1, events)

        assert projection.summary.characteristics[Chars.SOC] == 6  # 7-1

    def test_graduation_queues_three_skill_picks_at_level_zero(self):
        events = _precareer_graduation_events(
            SchoolOfHardKnocksPreCareer, entry_roll=5, skills=[Athletics(), Deception()], graduation_roll=9
        )
        projection = replay(1, events)

        picks = [p for p in projection.pending_inputs if isinstance(p, PendingPreCareerSkillChoice)]
        assert len(picks) == 3
        assert all(p.level == 0 for p in picks)

    def test_graduation_queues_career_choice_with_distinct_id(self):
        events = _precareer_graduation_events(
            SchoolOfHardKnocksPreCareer, entry_roll=5, skills=[Athletics(), Deception()], graduation_roll=9
        )
        projection = replay(1, events)

        career_choices = [p for p in projection.pending_inputs if isinstance(p, PendingCareerChoice)]
        assert len(career_choices) == 1
        pick_ids = {p.id for p in projection.pending_inputs if isinstance(p, PendingPreCareerSkillChoice)}
        assert career_choices[0].id not in pick_ids

    def test_graduation_adds_dm_minus_two_problem(self):
        events = _precareer_graduation_events(
            SchoolOfHardKnocksPreCareer, entry_roll=5, skills=[Athletics(), Deception()], graduation_roll=9
        )
        projection = replay(1, events)

        assert any('DM-2' in p for p in projection.summary.problems)

    def test_honours_graduation_grants_carouse_at_level_one(self):
        events = _precareer_graduation_events(
            SchoolOfHardKnocksPreCareer, entry_roll=5, skills=[Athletics(), Deception()], graduation_roll=11
        )
        projection = replay(1, events)

        assert _skill_level(projection, 'Carouse') >= 1

    def test_honours_graduation_queues_four_picks_including_one_at_level_one(self):
        events = _precareer_graduation_events(
            SchoolOfHardKnocksPreCareer, entry_roll=5, skills=[Athletics(), Deception()], graduation_roll=11
        )
        projection = replay(1, events)

        picks = [p for p in projection.pending_inputs if isinstance(p, PendingPreCareerSkillChoice)]
        assert len(picks) == 4
        assert sum(1 for p in picks if p.level == 1) == 1

    def test_honours_career_choice_id_distinct_from_four_picks(self):
        events = _precareer_graduation_events(
            SchoolOfHardKnocksPreCareer, entry_roll=5, skills=[Athletics(), Deception()], graduation_roll=11
        )
        projection = replay(1, events)

        career_choices = [p for p in projection.pending_inputs if isinstance(p, PendingCareerChoice)]
        pick_ids = {p.id for p in projection.pending_inputs if isinstance(p, PendingPreCareerSkillChoice)}
        assert len(career_choices) == 1
        assert career_choices[0].id not in pick_ids


# ── Spacer Community ─────────────────────────────────────────────────────────


class TestSpacerCommunity:
    def test_entry_auto_grants_vacc_suit_at_level_one(self):
        events = _precareer_entry_events(SpacerCommunityPreCareer, 5)
        projection = replay(1, events)

        assert _skill_level(projection, 'Vacc Suit') >= 1

    def test_entry_queues_two_skill_picks_at_level_zero(self):
        events = _precareer_entry_events(SpacerCommunityPreCareer, 5)
        projection = replay(1, events)

        picks = [p for p in projection.pending_inputs if isinstance(p, PendingPreCareerSkillChoice)]
        assert len(picks) == 2
        assert all(p.level == 0 for p in picks)

    def test_entry_pick_pool_excludes_auto_granted_vacc_suit(self):
        events = _precareer_entry_events(SpacerCommunityPreCareer, 5)
        projection = replay(1, events)

        picks = [p for p in projection.pending_inputs if isinstance(p, PendingPreCareerSkillChoice)]
        assert not any(type(o).name() == 'Vacc Suit' for o in picks[0].options)
        assert any(isinstance(o, Astrogation) for o in picks[0].options)

    def test_graduation_grants_pilot(self):
        # DEX=7 (>=6) → graduation_dms DEX_6+ applies: effective = roll + DM(INT=7) + 1 = roll+1
        events = _precareer_graduation_events(
            SpacerCommunityPreCareer, entry_roll=5, skills=[Astrogation(), Electronics()], graduation_roll=9
        )
        projection = replay(1, events)

        assert _skill_level(projection, 'Pilot') >= 0

    def test_graduation_increases_dex_by_one(self):
        events = _precareer_graduation_events(
            SpacerCommunityPreCareer, entry_roll=5, skills=[Astrogation(), Electronics()], graduation_roll=9
        )
        projection = replay(1, events)

        assert projection.summary.characteristics[Chars.DEX] == 8  # 7+1

    def test_graduation_decreases_soc_by_two(self):
        events = _precareer_graduation_events(
            SpacerCommunityPreCareer, entry_roll=5, skills=[Astrogation(), Electronics()], graduation_roll=9
        )
        projection = replay(1, events)

        assert projection.summary.characteristics[Chars.SOC] == 5  # 7-2

    def test_graduation_queues_two_level_zero_and_one_level_one_pick(self):
        events = _precareer_graduation_events(
            SpacerCommunityPreCareer, entry_roll=5, skills=[Astrogation(), Electronics()], graduation_roll=9
        )
        projection = replay(1, events)

        picks = [p for p in projection.pending_inputs if isinstance(p, PendingPreCareerSkillChoice)]
        assert len(picks) == 3
        assert sum(1 for p in picks if p.level == 0) == 2
        assert sum(1 for p in picks if p.level == 1) == 1

    def test_graduation_adds_qualification_dm(self):
        events = _precareer_graduation_events(
            SpacerCommunityPreCareer, entry_roll=5, skills=[Astrogation(), Electronics()], graduation_roll=9
        )
        projection = replay(1, events)

        assert projection.pending_qualification_dm == 1

    def test_graduation_queues_career_choice_with_distinct_id(self):
        events = _precareer_graduation_events(
            SpacerCommunityPreCareer, entry_roll=5, skills=[Astrogation(), Electronics()], graduation_roll=9
        )
        projection = replay(1, events)

        career_choices = [p for p in projection.pending_inputs if isinstance(p, PendingCareerChoice)]
        assert len(career_choices) == 1
        pick_ids = {p.id for p in projection.pending_inputs if isinstance(p, PendingPreCareerSkillChoice)}
        assert career_choices[0].id not in pick_ids

    def test_honours_graduation_grants_jack_of_all_trades(self):
        events = _precareer_graduation_events(
            SpacerCommunityPreCareer, entry_roll=5, skills=[Astrogation(), Electronics()], graduation_roll=11
        )
        projection = replay(1, events)

        assert _skill_level(projection, 'Jack-of-All-Trades') >= 1


class TestUniversity:
    # _base() uses EDU=0 (no background skills). University requires EDU 6+; with EDU=0 (DM-3),
    # a roll of 9 yields effective 6, which just passes. All tests use roll=9 for entry.

    def test_entry_queues_level_zero_and_level_one_skill_picks(self):
        events = _precareer_entry_events(UniversityPreCareer, 9)
        projection = replay(1, events)

        picks = [p for p in projection.pending_inputs if isinstance(p, PendingPreCareerSkillChoice)]
        assert sum(1 for p in picks if p.level == 0) == 1
        assert sum(1 for p in picks if p.level == 1) == 1

    def test_level_one_options_contain_specialisation_labels_not_base_names(self):
        events = _precareer_entry_events(UniversityPreCareer, 9)
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
        events = _precareer_entry_events(UniversityPreCareer, 9)
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
        events = _precareer_entry_events(UniversityPreCareer, 9)
        entry = events[-1]
        events.append(_event(fulfills=_pending(entry, 0), handler=PreCareerSkillChoiceHandler(skill=Admin())))
        events.append(
            _event(
                fulfills=_pending(entry, 1),
                handler=PreCareerSkillChoiceHandler(skill=PhysicalScience(chemistry=Level(value=1))),
            )
        )
        projection = replay(1, events)

        ps_skill = next((s for s in projection.summary.skills if type(s).name() == 'Physical Science'), None)
        assert ps_skill is not None
        assert isinstance(ps_skill, PhysicalScience)
        assert ps_skill.chemistry.value == 1
        assert ps_skill.physics.value == 0
        assert ps_skill.jumpspace_physics.value == 0

    def test_graduation_increments_chosen_specialisation_not_all(self):
        # After graduation, Physical Science (Chemistry) 1 should become Chemistry 2, not all specs 2.
        events = _precareer_graduation_events(
            UniversityPreCareer,
            entry_roll=9,
            skills=[Admin(), PhysicalScience(chemistry=Level(value=1))],
            graduation_roll=8,
        )
        projection = replay(1, events)

        ps_skill = next((s for s in projection.summary.skills if type(s).name() == 'Physical Science'), None)
        assert ps_skill is not None
        assert isinstance(ps_skill, PhysicalScience)
        assert ps_skill.chemistry.value == 2
        assert ps_skill.physics.value == 0
        assert ps_skill.jumpspace_physics.value == 0


# ── precareer field typing ────────────────────────────────────────────────────


def test_precareer_in_progress_is_typed_object():
    events = _precareer_entry_events(UniversityPreCareer, 9)
    projection = replay(1, events)
    assert isinstance(projection.summary.precareer, PreCareerData)
    assert projection.summary.precareer.name == 'University'


def test_precareer_completed_is_typed_object():
    events = _precareer_graduation_events(
        UniversityPreCareer, entry_roll=9, skills=[Admin(), Electronics()], graduation_roll=9
    )
    projection = replay(1, events)
    assert isinstance(projection.summary.precareer_completed, PreCareerData)
    assert projection.summary.precareer_completed.name == 'University'
    assert projection.summary.precareer is None
