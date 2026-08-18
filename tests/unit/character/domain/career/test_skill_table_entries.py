"""Unit tests for skill table entry types."""

from pydantic import TypeAdapter
import pytest

from ceres.character.domain.career import ARMY
from ceres.character.domain.career.career_data import CareerTerm
from ceres.character.domain.career.career_events import (
    PendingSkillTableChoice,
    SkillTableEntryChosenHandler,
    SkillTableHandler,
    SurviveHandler,
)
from ceres.character.domain.career.skill_table_entries import (
    Char,
    Psi as PsiEntry,
    PsiChoice,
    Skill,
    SkillChoice,
    SkillTableApplyContext,
    SkillTableItem,
    expand_skill_classes,
    expand_talent_classes,
)
from ceres.character.domain.character_state import CharacterProjection, CharacterSummary
from ceres.character.domain.characteristics import Chars
from ceres.character.domain.psionics import PendingPsionicInstituteTraining
from ceres.character.domain.psionics_data import (
    Awareness,
    Clairvoyance,
    Psionics,
    Telekinesis,
    Telepathy,
    Teleportation,
)
from ceres.character.domain.skills import (
    Admin,
    AnySkill,
    Athletics,
    Electronics,
    Gambler,
    GunCombat,
    LanguageSkill,
    Level,
    Melee,
    Navigation,
    Recon,
    Seafarer,
    Tactics,
)
from ceres.character.input_specs import Select
from ceres.character.mechanism.event_base import Event


def _event(event_id: int = 1) -> Event:
    return Event(id=event_id, handler=SurviveHandler(roll=5))


def _projection() -> CharacterProjection:
    return CharacterProjection(character_id=1, summary=CharacterSummary(name='Test'))


def _ctx(event_id: int = 1) -> SkillTableApplyContext:
    return SkillTableApplyContext(event=_event(event_id))


class TestSkillTableApplyContext:
    def test_first_id_uses_event_id_and_index_zero(self):
        ctx = _ctx(event_id=42)
        assert ctx.next_pending_id() == (42, 0)

    def test_subsequent_calls_increment_index(self):
        ctx = _ctx(event_id=7)
        ctx.next_pending_id()
        assert ctx.next_pending_id() == (7, 1)
        assert ctx.next_pending_id() == (7, 2)

    def test_separate_contexts_have_independent_counters(self):
        ctx_a = _ctx(event_id=1)
        ctx_b = _ctx(event_id=1)
        ctx_a.next_pending_id()
        ctx_a.next_pending_id()
        assert ctx_b.next_pending_id() == (1, 0)

    def test_level_defaults_to_none(self):
        ctx = _ctx()
        assert ctx.level is None

    def test_level_can_be_set(self):
        ctx = SkillTableApplyContext(event=_event(), level=0)
        assert ctx.level == 0


class TestChar:
    def test_positional_constructor(self):
        char = Char(Chars.STR)
        assert char.characteristic == Chars.STR

    def test_round_trip_via_skill_table_item_adapter(self):
        adapter = TypeAdapter(SkillTableItem)
        char = Char(Chars.END)
        data = char.model_dump()
        parsed = adapter.validate_python(data)
        assert isinstance(parsed, Char)
        assert parsed.characteristic == Chars.END

    def test_apply_increments_characteristic_from_zero(self):
        projection = _projection()
        Char(Chars.STR).apply(projection, _ctx())
        assert projection.summary.characteristics[Chars.STR] == 1

    def test_apply_increments_existing_characteristic(self):
        projection = CharacterProjection(
            character_id=1,
            summary=CharacterSummary(name='Test', characteristics={Chars.STR: 7}),
        )
        Char(Chars.STR).apply(projection, _ctx())
        assert projection.summary.characteristics[Chars.STR] == 8

    def test_apply_does_not_affect_other_characteristics(self):
        projection = CharacterProjection(
            character_id=1,
            summary=CharacterSummary(name='Test', characteristics={Chars.DEX: 5}),
        )
        Char(Chars.STR).apply(projection, _ctx())
        assert projection.summary.characteristics.get(Chars.DEX) == 5

    def test_label_names_the_characteristic(self):
        assert 'STR' in Char(Chars.STR).label()


class TestSkillEntry:
    def test_positional_constructor(self):
        entry = Skill(Admin)
        assert entry.skill is Admin

    def test_level_defaults_to_none(self):
        assert Skill(Admin).level is None

    def test_level_can_be_set(self):
        assert Skill(Admin, level=1).level == 1

    def test_skill_class_round_trips_via_adapter(self):
        adapter = TypeAdapter(SkillTableItem)
        entry = Skill(Admin)
        data = entry.model_dump()
        parsed = adapter.validate_python(data)
        assert isinstance(parsed, Skill)
        assert parsed.skill is Admin

    def test_apply_increments_unknown_skill_to_level_one(self):
        proj = _projection()
        Skill(Admin).apply(proj, _ctx())
        assert proj.summary.skill_level(Admin) == 1

    def test_apply_increments_existing_skill(self):
        proj = _projection()
        proj.summary.skills.append(Admin(level=Level(value=1)))
        Skill(Admin).apply(proj, _ctx())
        assert proj.summary.skill_level(Admin) == 2

    def test_apply_level_zero_grants_unknown_skill_at_zero(self):
        proj = _projection()
        ctx = SkillTableApplyContext(event=_event(), level=0)
        Skill(Admin).apply(proj, ctx)
        assert proj.summary.skill_level(Admin) == 0

    def test_apply_level_zero_does_not_overwrite_existing(self):
        proj = _projection()
        proj.summary.skills.append(Admin(level=Level(value=2)))
        ctx = SkillTableApplyContext(event=_event(), level=0)
        Skill(Admin).apply(proj, ctx)
        assert proj.summary.skill_level(Admin) == 2

    def test_apply_entry_level_grants_skill_at_that_level(self):
        proj = _projection()
        Skill(Admin, level=1).apply(proj, _ctx())
        assert proj.summary.skill_level(Admin) == 1

    def test_apply_entry_level_does_not_lower_higher_skill(self):
        proj = _projection()
        proj.summary.skills.append(Admin(level=Level(value=3)))
        Skill(Admin, level=1).apply(proj, _ctx())
        assert proj.summary.skill_level(Admin) == 3

    def test_apply_multi_spec_increment_queues_skill_table_choice(self):
        # Electronics has multiple specialization fields; increment mode queues a choice
        proj = _projection()
        Skill(Electronics).apply(proj, _ctx())
        pendings = [p for p in proj.pending_inputs if isinstance(p, PendingSkillTableChoice)]
        assert len(pendings) == 1
        assert any(isinstance(opt, Electronics) for opt in pendings[0].options)

    def test_apply_multi_spec_increment_does_not_directly_grant_skill(self):
        proj = _projection()
        Skill(Electronics).apply(proj, _ctx())
        assert proj.summary.skill_level(Electronics) is None

    def test_apply_multi_spec_level_zero_grants_base_skill_no_choice(self):
        # Level-0 (basic training): grant base skill directly, no specialization choice
        proj = _projection()
        ctx = SkillTableApplyContext(event=_event(), level=0)
        Skill(Electronics).apply(proj, ctx)
        assert proj.summary.skill_level(Electronics) == 0
        assert not any(isinstance(p, PendingSkillTableChoice) for p in proj.pending_inputs)

    def test_ctx_level_overrides_entry_level(self):
        # ctx.level=0 (basic training) wins over entry.level=1
        proj = _projection()
        proj.summary.skills.append(Admin(level=Level(value=1)))
        ctx = SkillTableApplyContext(event=_event(), level=0)
        Skill(Admin, level=2).apply(proj, ctx)
        assert proj.summary.skill_level(Admin) == 1  # unchanged: ctx.level=0 → no overwrite


class TestSkillEntrySpecs:
    """Skill entries can restrict the specialization choice via typed SpecRefs."""

    def test_specs_default_to_none(self):
        assert Skill(Tactics).specs is None

    def test_specs_are_stored_as_spec_refs(self):
        entry = Skill(Seafarer, specs=(Seafarer.personal, Seafarer.sail))
        assert entry.specs is not None
        assert [ref.field for ref in entry.specs] == ['personal', 'sail']
        assert all(ref.skill_cls is Seafarer for ref in entry.specs)

    def test_spec_from_other_skill_class_is_rejected(self):
        with pytest.raises(ValueError):
            Skill(Melee, specs=(Electronics.comms,))

    def test_specs_round_trip_via_skill_table_item_adapter(self):
        adapter = TypeAdapter(SkillTableItem)
        entry = Skill(Seafarer, specs=(Seafarer.personal, Seafarer.sail))
        parsed = adapter.validate_python(entry.model_dump())
        assert isinstance(parsed, Skill)
        assert parsed.specs is not None
        assert [ref.field for ref in parsed.specs] == ['personal', 'sail']
        assert all(ref.skill_cls is Seafarer for ref in parsed.specs)

    def test_apply_level_with_single_spec_grants_that_specialization(self):
        # e.g. army advanced education: Tactics (military) 1
        proj = _projection()
        Skill(Tactics, level=1, specs=(Tactics.military,)).apply(proj, _ctx())
        granted = next(s for s in proj.summary.skills if isinstance(s, Tactics))
        assert granted.military.value == 1
        assert granted.naval.value == 0

    def test_apply_level_with_single_spec_does_not_queue_pending(self):
        proj = _projection()
        Skill(Tactics, level=1, specs=(Tactics.military,)).apply(proj, _ctx())
        assert proj.pending_inputs == ()

    def test_apply_increment_with_single_spec_increments_that_specialization(self):
        proj = _projection()
        proj.summary.skills.append(Tactics(military=Level(value=1)))
        Skill(Tactics, specs=(Tactics.military,)).apply(proj, _ctx())
        granted = next(s for s in proj.summary.skills if isinstance(s, Tactics))
        assert granted.military.value == 2

    def test_apply_increment_with_multiple_specs_queues_restricted_choice(self):
        # Drifter Barbarian: Seafarer (personal or sail)
        proj = _projection()
        Skill(Seafarer, specs=(Seafarer.personal, Seafarer.sail)).apply(proj, _ctx())
        pending = next(p for p in proj.pending_inputs if isinstance(p, PendingSkillTableChoice))
        select = next(s for s in pending.input_specs(proj) if isinstance(s, Select))
        labels = [label for label, _ in select.options]
        assert labels == ['Seafarer (Personal)', 'Seafarer (Sail)']

    def test_apply_level_with_multiple_specs_queues_restricted_choice(self):
        # Scout: Pilot (small craft or spacecraft) 1
        proj = _projection()
        Skill(Seafarer, level=1, specs=(Seafarer.personal, Seafarer.sail)).apply(proj, _ctx())
        pending = next(p for p in proj.pending_inputs if isinstance(p, PendingSkillTableChoice))
        select = next(s for s in pending.input_specs(proj) if isinstance(s, Select))
        labels = [label for label, _ in select.options]
        assert labels == ['Seafarer (Personal)', 'Seafarer (Sail)']

    def test_apply_level_zero_with_specs_grants_whole_skill(self):
        # Basic training grants the whole skill at level 0 regardless of spec restriction
        proj = _projection()
        ctx = SkillTableApplyContext(event=_event(), level=0)
        Skill(Seafarer, specs=(Seafarer.personal, Seafarer.sail)).apply(proj, ctx)
        assert proj.summary.skill_level(Seafarer) == 0
        assert not any(isinstance(p, PendingSkillTableChoice) for p in proj.pending_inputs)

    def test_unrestricted_multi_spec_choice_still_offers_all_specializations(self):
        proj = _projection()
        Skill(Seafarer).apply(proj, _ctx())
        pending = next(p for p in proj.pending_inputs if isinstance(p, PendingSkillTableChoice))
        select = next(s for s in pending.input_specs(proj) if isinstance(s, Select))
        assert len(select.options) == len(Seafarer.specialities())


class TestSkillHandlerIntegration:
    """Verify Skill entries route correctly through SkillTableHandler."""

    def _proj_with_army(self) -> CharacterProjection:
        proj = CharacterProjection(
            character_id=1,
            summary=CharacterSummary(name='Test'),
        )
        proj.summary.terms.append(CareerTerm(career=ARMY, assignment=ARMY.assignment('Infantry')))
        return proj

    def test_skill_table_handler_grants_skill_via_skill_entry(self):
        # After Step 2 migration, Army personal_development roll 4 = Skill(Gambler)
        proj = self._proj_with_army()
        event = Event(id=10, handler=SkillTableHandler(table='personal_development', roll=4))
        event.apply(proj)
        assert proj.summary.skill_level(Gambler) == 1

    def test_skill_table_handler_skill_entry_does_not_queue_pending(self):
        proj = self._proj_with_army()
        event = Event(id=10, handler=SkillTableHandler(table='personal_development', roll=4))
        event.apply(proj)
        assert proj.pending_inputs == ()


class TestSkillEntryDataMigration:
    """Verify that single-spec SkillTable entries have been migrated to Skill instances."""

    def test_army_personal_development_gambler_is_skill_entry(self):
        entry = ARMY.skill_table('personal_development').entries[3]
        assert isinstance(entry, Skill)
        assert entry.skill is Gambler

    def test_army_service_skills_recon_is_skill_entry(self):
        # Army service_skills: (Drive/VaccSuit), Athletics, GunCombat, Recon, Melee, HeavyWeapons
        entry = ARMY.skill_table('service_skills').entries[3]
        assert isinstance(entry, Skill)
        assert entry.skill is Recon

    def test_army_advanced_education_navigation_is_skill_entry(self):
        # Army advanced_education: Tactics(mil), Electronics, Navigation, Explosives, Engineer, Survival
        entry = ARMY.skill_table('advanced_education').entries[2]
        assert isinstance(entry, Skill)
        assert entry.skill is Navigation

    def test_army_service_skills_athletics_is_skill_entry(self):
        # Army service_skills: (Drive/VaccSuit), Athletics, GunCombat, Recon(Skill), Melee, HeavyWeapons
        entry = ARMY.skill_table('service_skills').entries[1]
        assert isinstance(entry, Skill)
        assert entry.skill is Athletics

    def test_army_advanced_education_electronics_is_skill_entry(self):
        entry = ARMY.skill_table('advanced_education').entries[1]
        assert isinstance(entry, Skill)
        assert entry.skill is Electronics


class TestCharHandlerIntegration:
    """Verify the bridge routes Char entries through SkillTableHandler correctly."""

    def _proj_with_army(self) -> CharacterProjection:
        proj = CharacterProjection(
            character_id=1,
            summary=CharacterSummary(name='Test', characteristics={Chars.STR: 5}),
        )
        proj.summary.terms.append(CareerTerm(career=ARMY, assignment=ARMY.assignment('Infantry')))
        return proj

    def test_skill_table_handler_increments_characteristic_via_char_entry(self):
        # Army personal_development roll 1 = Char(Chars.STR); verify the bridge fires apply()
        proj = self._proj_with_army()
        event = Event(id=10, handler=SkillTableHandler(table='personal_development', roll=1))
        event.apply(proj)
        assert proj.summary.characteristics[Chars.STR] == 6

    def test_skill_table_handler_char_entry_does_not_queue_pending(self):
        # Characteristic entries should apply immediately, not queue a pending choice
        proj = self._proj_with_army()
        event = Event(id=10, handler=SkillTableHandler(table='personal_development', roll=1))
        event.apply(proj)
        assert proj.pending_inputs == ()


def _proj_with_psionics(has_telepathy: bool = True) -> CharacterProjection:
    psionics = Psionics(
        psionic_talent_skills=[Telepathy()] if has_telepathy else [],
    )
    return CharacterProjection(
        character_id=1,
        summary=CharacterSummary(name='T', characteristics={Chars.PSI: 9}, psionics=psionics),
    )


class TestPsiEntry:
    def test_positional_constructor(self):
        entry = PsiEntry(Telepathy)
        assert entry.talent is Telepathy

    def test_allow_acquisition_defaults_to_false(self):
        assert PsiEntry(Telepathy).allow_acquisition is False

    def test_allow_acquisition_can_be_set(self):
        assert PsiEntry(Telepathy, allow_acquisition=True).allow_acquisition is True

    def test_apply_no_psi_not_gained(self):
        proj = CharacterProjection(character_id=1, summary=CharacterSummary(name='T'))
        PsiEntry(Telepathy).apply(proj, _ctx())
        assert proj.summary.psionics is None
        assert proj.summary.skill_level(Telepathy) is None

    def test_apply_possessed_talent_increments_level(self):
        proj = _proj_with_psionics(has_telepathy=True)
        assert proj.summary.psionics is not None
        assert proj.summary.psionics.talent_level(Telepathy) == 0
        PsiEntry(Telepathy, allow_acquisition=True).apply(proj, _ctx())
        assert proj.summary.psionics.talent_level(Telepathy) == 1

    def test_apply_possessed_talent_does_not_queue_pending(self):
        proj = _proj_with_psionics(has_telepathy=True)
        PsiEntry(Telepathy, allow_acquisition=True).apply(proj, _ctx())
        assert proj.pending_inputs == ()

    def test_apply_unpossessed_talent_with_acquisition_queues_institute_training(self):
        proj = _proj_with_psionics(has_telepathy=False)
        PsiEntry(Telepathy, allow_acquisition=True).apply(proj, _ctx())
        pendings = [p for p in proj.pending_inputs if isinstance(p, PendingPsionicInstituteTraining)]
        assert len(pendings) == 1
        assert any(isinstance(t, Telepathy) for t in pendings[0].remaining_talents)

    def test_apply_unpossessed_talent_without_acquisition_not_gained(self):
        proj = _proj_with_psionics(has_telepathy=False)
        PsiEntry(Telepathy, allow_acquisition=False).apply(proj, _ctx())
        assert not any(isinstance(p, PendingPsionicInstituteTraining) for p in proj.pending_inputs)
        assert proj.summary.psionics is not None
        assert proj.summary.psionics.talent_level(Telepathy) is None

    def test_apply_uses_ctx_next_pending_id(self):
        proj = _proj_with_psionics(has_telepathy=False)
        ctx = SkillTableApplyContext(event=_event(event_id=42))
        ctx.next_pending_id()  # advance idx to 1
        PsiEntry(Telepathy, allow_acquisition=True).apply(proj, ctx)
        pending = next(p for p in proj.pending_inputs if isinstance(p, PendingPsionicInstituteTraining))
        assert pending.pending_id == (42, 1)


class TestExpandSkillClasses:
    def test_single_class_returns_that_class(self):
        result = expand_skill_classes(Admin)
        assert result == (Admin,)

    def test_two_class_union_returns_both(self):
        result = expand_skill_classes(Melee | GunCombat)
        assert result == (Melee, GunCombat)

    def test_broad_alias_expands_to_all_member_classes(self):
        result = expand_skill_classes(LanguageSkill)
        assert len(result) > 1
        from ceres.character.domain.skills import LanguageGalanglic, LanguageVilani

        assert LanguageGalanglic in result
        assert LanguageVilani in result

    def test_invalid_input_raises_value_error(self):
        with pytest.raises(ValueError):
            expand_skill_classes(object)

    def test_all_results_are_skill_classes(self):
        from ceres.character.domain.skills import Skill as SkillModel

        for cls in expand_skill_classes(Melee | GunCombat | Admin):
            assert isinstance(cls, type) and issubclass(cls, SkillModel)


class TestExpandTalentClasses:
    def test_two_talent_union_returns_both(self):
        result = expand_talent_classes(Telepathy | Clairvoyance)
        assert result == (Telepathy, Clairvoyance)

    def test_all_five_talents_union(self):
        result = expand_talent_classes(Telepathy | Clairvoyance | Telekinesis | Awareness | Teleportation)
        assert set(result) == {Telepathy, Clairvoyance, Telekinesis, Awareness, Teleportation}

    def test_invalid_input_raises_value_error(self):
        with pytest.raises(ValueError):
            expand_talent_classes(object)


class TestSkillChoice:
    def test_positional_constructor(self):
        entry = SkillChoice(Melee | GunCombat)
        assert set(entry.skills) == {Melee, GunCombat}

    def test_apply_queues_pending_skill_table_choice(self):
        proj = _projection()
        SkillChoice(Melee | GunCombat).apply(proj, _ctx())
        pendings = [p for p in proj.pending_inputs if isinstance(p, PendingSkillTableChoice)]
        assert len(pendings) == 1

    def test_apply_options_are_concrete_skill_entries(self):
        proj = _projection()
        SkillChoice(Melee | GunCombat).apply(proj, _ctx())
        pending = next(p for p in proj.pending_inputs if isinstance(p, PendingSkillTableChoice))
        assert all(isinstance(opt, Skill) for opt in pending.options)
        skill_classes = {opt.skill for opt in pending.options if isinstance(opt, Skill)}
        assert skill_classes == {Melee, GunCombat}

    def test_apply_uses_ctx_next_pending_id(self):
        proj = _projection()
        ctx = SkillTableApplyContext(event=_event(event_id=7))
        ctx.next_pending_id()
        SkillChoice(Melee | GunCombat).apply(proj, ctx)
        pending = next(p for p in proj.pending_inputs if isinstance(p, PendingSkillTableChoice))
        assert pending.pending_id == (7, 1)

    def test_apply_single_class_queues_one_option(self):
        proj = _projection()
        SkillChoice(Admin).apply(proj, _ctx())
        pending = next(p for p in proj.pending_inputs if isinstance(p, PendingSkillTableChoice))
        assert len(pending.options) == 1
        opt = pending.options[0]
        assert isinstance(opt, Skill) and opt.skill is Admin


class TestSkillChoiceSpecs:
    """A SkillChoice spec restricts only its own class; unmentioned classes offer any specialization."""

    def test_specs_default_to_none(self):
        assert SkillChoice(GunCombat | Melee).specs is None

    def test_spec_for_class_outside_union_is_rejected(self):
        with pytest.raises(ValueError):
            SkillChoice(GunCombat | Melee, specs=(Electronics.comms,))

    def test_apply_restricts_only_the_spec_owning_class(self):
        # Marine rank 0 shape: Gun Combat (any) or Melee (blade)
        proj = _projection()
        SkillChoice(GunCombat | Melee, specs=(Melee.blade,)).apply(proj, _ctx())
        pending = next(p for p in proj.pending_inputs if isinstance(p, PendingSkillTableChoice))
        gun_combat = next(o for o in pending.options if isinstance(o, Skill) and o.skill is GunCombat)
        melee = next(o for o in pending.options if isinstance(o, Skill) and o.skill is Melee)
        assert gun_combat.specs is None
        assert melee.specs is not None
        assert [ref.field for ref in melee.specs] == ['blade']

    def test_restricted_options_marks_restriction_per_class(self):
        choice = SkillChoice(GunCombat | Melee, specs=(Melee.blade,))
        gun_combat, melee = choice.restricted_options()
        assert isinstance(gun_combat, GunCombat)
        assert all(getattr(gun_combat, f).value == 0 for f in ('archaic', 'energy', 'slug'))
        assert isinstance(melee, Melee)
        assert melee.blade.value == 1
        assert melee.unarmed.value == 0


class TestPsiChoice:
    def test_positional_constructor(self):
        entry = PsiChoice(Telepathy | Clairvoyance)
        assert entry.allow_acquisition is False

    def test_allow_acquisition_can_be_set(self):
        entry = PsiChoice(Telepathy | Clairvoyance, allow_acquisition=True)
        assert entry.allow_acquisition is True

    def test_apply_no_psi_queues_nothing(self):
        proj = CharacterProjection(character_id=1, summary=CharacterSummary(name='T'))
        PsiChoice(Telepathy | Clairvoyance, allow_acquisition=True).apply(proj, _ctx())
        assert not any(isinstance(p, PendingSkillTableChoice) for p in proj.pending_inputs)

    def test_apply_with_psi_allow_acquisition_queues_all_talents(self):
        proj = _proj_with_psionics(has_telepathy=False)  # PSI but no Telepathy
        PsiChoice(Telepathy | Clairvoyance, allow_acquisition=True).apply(proj, _ctx())
        pending = next(p for p in proj.pending_inputs if isinstance(p, PendingSkillTableChoice))
        assert len(pending.options) == 2
        talent_classes = {opt.talent for opt in pending.options if isinstance(opt, PsiEntry)}
        assert talent_classes == {Telepathy, Clairvoyance}

    def test_apply_options_carry_allow_acquisition_flag(self):
        proj = _proj_with_psionics(has_telepathy=False)
        PsiChoice(Telepathy | Clairvoyance, allow_acquisition=True).apply(proj, _ctx())
        pending = next(p for p in proj.pending_inputs if isinstance(p, PendingSkillTableChoice))
        assert all(opt.allow_acquisition is True for opt in pending.options if isinstance(opt, PsiEntry))

    def test_apply_no_acquisition_filters_to_possessed_only(self):
        proj = _proj_with_psionics(has_telepathy=True)  # has Telepathy, not Clairvoyance
        PsiChoice(Telepathy | Clairvoyance, allow_acquisition=False).apply(proj, _ctx())
        pending = next(p for p in proj.pending_inputs if isinstance(p, PendingSkillTableChoice))
        assert len(pending.options) == 1
        opt = pending.options[0]
        assert isinstance(opt, PsiEntry) and opt.talent is Telepathy

    def test_apply_no_acquisition_no_possessed_talents_queues_nothing(self):
        proj = _proj_with_psionics(has_telepathy=False)  # has PSI, no Telepathy or Clairvoyance
        PsiChoice(Telepathy | Clairvoyance, allow_acquisition=False).apply(proj, _ctx())
        assert not any(isinstance(p, PendingSkillTableChoice) for p in proj.pending_inputs)


class TestSkillTableEntryChosenHandler:
    def test_skill_entry_chosen_increments_skill(self):
        from ceres.character.domain.career.career_events import SkillTableEntryChosenHandler

        proj = _projection()
        event = Event(id=10, handler=SkillTableEntryChosenHandler(entry=Skill(Admin)))
        event.apply(proj)
        assert proj.summary.skill_level(Admin) == 1

    def test_psi_entry_chosen_increments_possessed_talent(self):
        from ceres.character.domain.career.career_events import SkillTableEntryChosenHandler

        proj = _proj_with_psionics(has_telepathy=True)
        event = Event(id=10, handler=SkillTableEntryChosenHandler(entry=PsiEntry(Telepathy)))
        event.apply(proj)
        assert proj.summary.psionics is not None
        assert proj.summary.psionics.talent_level(Telepathy) == 1

    def test_psi_entry_chosen_with_acquisition_queues_institute_training(self):
        from ceres.character.domain.career.career_events import SkillTableEntryChosenHandler

        proj = _proj_with_psionics(has_telepathy=False)
        event = Event(id=10, handler=SkillTableEntryChosenHandler(entry=PsiEntry(Telepathy, allow_acquisition=True)))
        event.apply(proj)
        pendings = [p for p in proj.pending_inputs if isinstance(p, PendingPsionicInstituteTraining)]
        assert len(pendings) == 1


class TestPendingSkillTableChoiceFormBoundary:
    """Web form boundary: input_specs() and event_from_form() for Skill/Psi wrapper options."""

    def _pending_skill_choice(self, *skill_cls: type[AnySkill]) -> PendingSkillTableChoice:
        return PendingSkillTableChoice(
            pending_id=(1, 0),
            instruction='Choose a skill',
            options=[Skill(cls) for cls in skill_cls],
        )

    def test_input_specs_renders_skill_wrapper_options(self):
        proj = _projection()
        pending = self._pending_skill_choice(Admin, Melee)
        specs = pending.input_specs(proj)
        select = next(s for s in specs if isinstance(s, Select))
        labels = [label for label, _ in select.options]
        assert Admin.name() in labels
        assert Melee.name() in labels

    def test_event_from_form_with_skill_wrapper_produces_entry_chosen_handler(self):
        pending = self._pending_skill_choice(Admin)
        event = pending.event_from_form({'skill': Skill(Admin).model_dump_json()})
        assert isinstance(event.handler, SkillTableEntryChosenHandler)
        assert event.handler.entry.skill is Admin  # ty: ignore[unresolved-attribute]

    def test_skill_choice_round_trip_grants_skill(self):
        proj = _projection()
        pending = self._pending_skill_choice(Admin)
        event = pending.event_from_form({'skill': Skill(Admin).model_dump_json()})
        event.apply(proj, pending)
        assert proj.summary.skill_level(Admin) == 1

    def test_input_specs_renders_psi_wrapper_options(self):
        proj = _proj_with_psionics(has_telepathy=False)
        pending = PendingSkillTableChoice(
            pending_id=(1, 0),
            instruction='Choose a talent',
            options=[PsiEntry(Telepathy, allow_acquisition=True)],
        )
        specs = pending.input_specs(proj)
        select = next(s for s in specs if isinstance(s, Select))
        labels = [label for label, _ in select.options]
        assert Telepathy.name() in labels

    def test_event_from_form_with_psi_wrapper_produces_entry_chosen_handler(self):
        pending = PendingSkillTableChoice(
            pending_id=(1, 0),
            instruction='Choose a talent',
            options=[PsiEntry(Telepathy, allow_acquisition=True)],
        )
        event = pending.event_from_form({'skill': PsiEntry(Telepathy, allow_acquisition=True).model_dump_json()})
        assert isinstance(event.handler, SkillTableEntryChosenHandler)
        assert event.handler.entry.talent is Telepathy  # ty: ignore[unresolved-attribute]

    def test_psi_wrapper_options_do_not_add_acquisition_roll_field(self):
        """Psi table entries handle the roll via PendingPsionicInstituteTraining — not on this form."""
        proj = _proj_with_psionics(has_telepathy=False)
        pending = PendingSkillTableChoice(
            pending_id=(1, 0),
            instruction='Choose a talent',
            options=[PsiEntry(Telepathy, allow_acquisition=True)],
        )
        from ceres.character.input_specs import NumberEntry

        specs = pending.input_specs(proj)
        assert not any(isinstance(s, NumberEntry) for s in specs)


class TestBasicTrainingCandidates:
    """Each entry type knows its own basic-training contribution — no isinstance dispatch needed."""

    def test_char_contributes_nothing(self):
        proj = _projection()
        assert Char(Chars.STR).basic_training_candidates(proj) == ()

    def test_skill_unknown_returns_instance(self):
        proj = _projection()
        candidates = Skill(Admin).basic_training_candidates(proj)
        assert len(candidates) == 1
        assert isinstance(candidates[0], Admin)

    def test_skill_already_known_returns_empty(self):
        proj = _projection()
        proj.summary.skills.append(Admin())
        assert Skill(Admin).basic_training_candidates(proj) == ()

    def test_psi_entry_contributes_nothing(self):
        proj = _proj_with_psionics(has_telepathy=True)
        assert PsiEntry(Telepathy).basic_training_candidates(proj) == ()

    def test_psi_choice_contributes_nothing(self):
        proj = _proj_with_psionics(has_telepathy=True)
        assert PsiChoice(Telepathy | Clairvoyance).basic_training_candidates(proj) == ()

    def test_skill_choice_returns_unknown_skills(self):
        proj = _projection()
        candidates = SkillChoice(Admin | Melee).basic_training_candidates(proj)
        assert {type(c) for c in candidates} == {Admin, Melee}

    def test_skill_choice_filters_known_skills(self):
        proj = _projection()
        proj.summary.skills.append(Admin())
        candidates = SkillChoice(Admin | Melee).basic_training_candidates(proj)
        assert len(candidates) == 1
        assert isinstance(candidates[0], Melee)

    def test_skill_choice_all_known_returns_empty(self):
        proj = _projection()
        proj.summary.skills.append(Admin())
        proj.summary.skills.append(Melee())
        assert SkillChoice(Admin | Melee).basic_training_candidates(proj) == ()
