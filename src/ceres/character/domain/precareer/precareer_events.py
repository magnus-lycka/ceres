from typing import Any, Literal, cast

from pydantic import Field

from ceres.character.domain.character_state import CharacterProjection
from ceres.character.domain.skills import AnySkill, _level_fields
from ceres.character.input_specs import InputSpec, NumberEntry, Select, form_int, form_str
from ceres.character.mechanism.errors import ReplayError
from ceres.character.mechanism.event_base import Event, EventHandlerBase
from ceres.character.mechanism.pending_input import PendingInputBase


def _expand_skill_to_spec_instances(skill: AnySkill) -> list[AnySkill]:
    """Return one instance per spec at Level(1) for specialised skills, or [skill] for unspecialised."""
    from ceres.character.domain.skills import Level

    skill_cls = type(skill)
    fields = _level_fields(skill_cls)
    if len(fields) <= 1:
        return [skill]
    cls: Any = skill_cls
    return [cast(AnySkill, cls(**{f: Level(value=1 if f == fn else 0) for f in fields})) for fn in fields]


class PreCareerEntryHandler(EventHandlerBase):
    kind: Literal['precareer_entry_event'] = 'precareer_entry_event'
    precareer: str
    roll: int  # 2D result for entry check (before characteristic DM)

    def apply(self, projection: Any, event: Event, fulfilled_pending: Any = None) -> None:
        from ceres.character.domain.career.career_events import queue_career_choice
        from ceres.character.domain.characteristics import Chars, characteristic_dm
        from ceres.character.domain.precareer.loader import load_precareers

        precareer = load_precareers().get(self.precareer)
        if precareer is None:
            raise ReplayError(f'Unknown pre-career: {self.precareer!r}')
        terms_started = projection.summary.terms_started_in_pre_and_careers
        if terms_started >= 3:
            raise ReplayError('Pre-career education is only available in terms 1–3')
        if projection.summary.precareer_completed is not None:
            raise ReplayError('A character may only attend one pre-career')
        dm = 0
        if precareer.entry is not None:
            char_val = projection.summary.characteristics.get(precareer.entry.characteristic, 0)
            dm += characteristic_dm(char_val)
            term_dm = precareer.entry_term_dms.get(terms_started + 1, 0)
            dm += term_dm
            if precareer.entry_soc_bonus_min is not None:
                soc = projection.summary.characteristics.get(Chars.SOC, 0)
                if soc >= precareer.entry_soc_bonus_min:
                    dm += precareer.entry_soc_bonus
            if self.roll == 2 or self.roll + dm < precareer.entry.target:
                queue_career_choice(projection, event.id, 'Pre-career entry failed — choose a career')
                return
        projection.summary.precareer = self.precareer
        projection.summary.age += 4
        pending_idx = 0
        pending_idx = precareer.apply_entry(projection, event, pending_idx)
        projection.pending_inputs.append(
            PendingPreCareerEvent(
                pending_id=(event.id, pending_idx),
                instruction='Roll 2D on Pre-career Events table',
            )
        )
        pending_idx += 1
        if precareer.graduation is not None:
            char = precareer.graduation.characteristic
            target = precareer.graduation.target
            dms_desc = ', '.join(f'{k}: DM{v:+d}' for k, v in precareer.graduation_dms.items())
            instruction = f'Graduation: {char} {target}+'
            if dms_desc:
                instruction += f' (DMs: {dms_desc})'
            projection.pending_inputs.append(
                PendingPreCareerGraduation(
                    pending_id=(event.id, pending_idx),
                    instruction=instruction,
                )
            )
        elif precareer.graduation_requirement is not None:
            projection.pending_inputs.append(
                PendingPreCareerGraduation(
                    pending_id=(event.id, pending_idx),
                    instruction=f'Graduation: {precareer.graduation_requirement}',
                )
            )


class PreCareerSkillChoiceHandler(EventHandlerBase):
    kind: Literal['precareer_skill_choice'] = 'precareer_skill_choice'
    skill: AnySkill

    model_config = {'arbitrary_types_allowed': True}

    def apply(self, projection: Any, event: Event, fulfilled_pending: Any = None) -> None:
        level = fulfilled_pending.level if isinstance(fulfilled_pending, PendingPreCareerSkillChoice) else 0
        if level == 0:
            projection.grant_skill(self.skill)
        else:
            projection.increment_skill(self.skill)
        projection.summary.precareer_skills.append(self.skill)


class PreCareerEventHandler(EventHandlerBase):
    kind: Literal['precareer_event'] = 'precareer_event'
    roll: int  # 2D result (2-12)

    def apply(self, projection: Any, event: Event, fulfilled_pending: Any = None) -> None:
        from ceres.character.domain.career.career_data import (
            AutoAdvanceEffect,
            CareerHandlerBase,
            DecreaseCharacteristicChoiceEffect,
            GainConnectionsRolledEffect,
            InjuryEffect,
            LifeEventEffect,
            RollMishapEffect,
            SkillChoiceEffect,
        )
        from ceres.character.domain.career.career_events import (
            PendingConnectionsRoll,
            PendingLifeEvent,
            PendingSkillChoice,
            queue_career_choice,
        )
        from ceres.character.domain.characteristics import Chars
        from ceres.character.domain.precareer.loader import load_precareers
        from ceres.character.domain.skills import AnySkill as _AnySkill, JackOfAllTrades, _skill_classes

        precareer_name = projection.summary.precareer
        if precareer_name is None:
            raise ReplayError('No active pre-career for pre-career event')
        precareer = load_precareers().get(precareer_name)
        if precareer is None:
            raise ReplayError(f'Unknown pre-career: {precareer_name!r}')
        term_event = precareer.events.get(self.roll)
        if term_event is None:
            raise ReplayError(f'No pre-career event entry for roll {self.roll}')
        projection.summary.narrative.append(f'Pre-career event ({precareer_name}): {term_event.text}')
        pending_idx = 0
        if self.roll in (3, 11):
            if self.roll == 11:
                projection.summary.problems.append(
                    f'Pre-career event 11: {term_event.text} '
                    'Consult rules: flee to Drifter or be drafted (1D: 1-3 Army, 4-5 Marine, 6 Navy). '
                    'You do not graduate this term. SOC 9+ may allow avoiding the draft.'
                )
            remaining_grad = [p for p in projection.pending_inputs if isinstance(p, PendingPreCareerGraduation)]
            for p in remaining_grad:
                projection.pending_inputs.remove(p)
            projection.summary.precareer_completed = precareer_name
            projection.summary.precareer = None
            queue_career_choice(projection, event.id, 'Pre-career ended (no graduation) — choose a career')
            return
        for effect in term_event.effects:
            if isinstance(effect, GainConnectionsRolledEffect):
                max_count = {'d3': 3, '1d3': 3, 'd6': 6}.get(effect.dice.lower(), 3)
                projection.pending_inputs.append(
                    PendingConnectionsRoll(
                        pending_id=(event.id, pending_idx),
                        connection_type=effect.connection_type,
                        instruction=f'Roll {effect.dice.upper()} for number of {effect.connection_type}s gained',
                        options=list(range(1, max_count + 1)),
                    )
                )
                pending_idx += 1
            elif isinstance(effect, SkillChoiceEffect):
                all_skills: list[_AnySkill] = sorted(
                    [cast(_AnySkill, cls()) for cls in _skill_classes(_AnySkill) if cls is not JackOfAllTrades],
                    key=lambda s: type(s).name(),
                )
                opts: list[_AnySkill] = cast(list[_AnySkill], effect.options) if effect.options else all_skills
                projection.pending_inputs.append(
                    PendingSkillChoice(
                        pending_id=(event.id, pending_idx),
                        instruction='Choose any skill at level 0',
                        options=opts,
                    )
                )
                pending_idx += 1
            elif isinstance(effect, LifeEventEffect):
                projection.pending_inputs.append(
                    PendingLifeEvent(
                        pending_id=(event.id, pending_idx),
                        instruction='Roll 2D on Life Events table',
                    )
                )
                pending_idx += 1
            elif isinstance(
                effect,
                (
                    DecreaseCharacteristicChoiceEffect,
                    InjuryEffect,
                    RollMishapEffect,
                    AutoAdvanceEffect,
                    CareerHandlerBase,
                ),
            ):
                pass
            else:
                effect.apply(projection, source=term_event.text, source_event_id=event.id)
        if self.roll == 12:
            projection.summary.characteristics[Chars.SOC] = projection.summary.characteristics.get(Chars.SOC, 0) + 1
        elif self.roll == 2:
            projection.summary.problems.append(
                'Pre-career event 2: you may test your PSI and attempt to enter the Psion career '
                'in any subsequent term (apply manually).'
            )
        elif self.roll == 4:
            projection.summary.problems.append(
                'Pre-career event 4: roll SOC 8+ — success: gain Rival; failure: gain Enemy. '
                'Natural 2: also fail to graduate and must take Prisoner career next term. Apply manually.'
            )


class PreCareerGraduationHandler(EventHandlerBase):
    kind: Literal['precareer_graduation'] = 'precareer_graduation'
    roll: int  # 2D result for graduation check (before characteristic DM)

    def apply(self, projection: Any, event: Event, fulfilled_pending: Any = None) -> None:
        from ceres.character.domain.career.career_events import queue_career_choice_indexed
        from ceres.character.domain.precareer.loader import load_precareers

        precareer_name = projection.summary.precareer
        if precareer_name is None:
            raise ReplayError('No active pre-career for graduation')
        precareer = load_precareers().get(precareer_name)
        if precareer is None:
            raise ReplayError(f'Unknown pre-career: {precareer_name!r}')

        from ceres.character.domain.characteristics import Chars, characteristic_dm

        graduated = True
        honours = False
        if precareer.graduation is not None:
            dm = characteristic_dm(projection.summary.characteristics.get(precareer.graduation.characteristic, 0))
            for key, dm_val in precareer.graduation_dms.items():
                try:
                    char_name, threshold_str = key.split('_', 1)
                    threshold = int(threshold_str.rstrip('+'))
                    char = Chars(char_name)
                    if projection.summary.characteristics.get(char, 0) >= threshold:
                        dm += dm_val
                except ValueError, KeyError:
                    pass
            effective = self.roll + dm
            graduated = self.roll != 2 and effective >= precareer.graduation.target
            if precareer.honours_target is not None:
                honours = effective >= precareer.honours_target
        elif precareer.honours_target is not None:
            honours = self.roll >= precareer.honours_target
        pending_graduation_idx = 0
        if graduated:
            projection.summary.narrative.append(
                f'Graduated from {precareer_name}' + (' with honours!' if honours else '.')
            )
            pending_graduation_idx = precareer.apply_graduation(projection, event, honours)
        else:
            projection.summary.narrative.append(f'Did not graduate from {precareer_name}.')
            precareer.apply_failed_graduation(projection, event)
        projection.summary.precareer_completed = precareer_name
        projection.summary.precareer = None
        projection.summary.precareer_skills = []
        queue_career_choice_indexed(
            projection, event.id, pending_graduation_idx, 'Pre-career complete — choose a career'
        )


# ── Precareer Pending Input Types ─────────────────────────────────────────────


class PendingPreCareerSkillChoice(PendingInputBase):
    kind: Literal['precareer_skill_choice'] = 'precareer_skill_choice'
    level: int
    options: list[AnySkill] = Field(default_factory=list)

    model_config = {'arbitrary_types_allowed': True}

    def _expanded_options(self) -> list[AnySkill]:
        if self.level == 0:
            return list(self.options)
        result: list[AnySkill] = []
        for skill in self.options:
            result.extend(_expand_skill_to_spec_instances(skill))
        return result

    def event_from_form(self, form: Any) -> Any:
        from pydantic import TypeAdapter

        from ceres.character.domain.skills import AnySkill as _AnySkill
        from ceres.character.mechanism.event_base import Event

        _skill_adapter: TypeAdapter[_AnySkill] = TypeAdapter(_AnySkill)
        skill = _skill_adapter.validate_json(form_str(form, 'skill', '{}'))
        return Event(fulfills=self.pending_id, handler=PreCareerSkillChoiceHandler(skill=skill))

    def input_specs(self, projection: CharacterProjection) -> list[InputSpec]:
        from ceres.character.domain.career.career_events import _skill_option_label

        options = [(_skill_option_label(opt), opt.model_dump_json()) for opt in self._expanded_options()]
        return [Select(name='skill', label='Choose a skill', options=options)]


class PendingPreCareerEvent(PendingInputBase):
    kind: Literal['precareer_event'] = 'precareer_event'

    def event_from_form(self, form: Any) -> Any:
        from ceres.character.mechanism.event_base import Event

        return Event(fulfills=self.pending_id, handler=PreCareerEventHandler(roll=form_int(form, 'roll', 7)))

    def input_specs(self, projection: CharacterProjection) -> list[InputSpec]:
        return [NumberEntry(name='roll', label='2D roll (2–12)', min=2, max=12)]


class PendingPreCareerGraduation(PendingInputBase):
    kind: Literal['precareer_graduation'] = 'precareer_graduation'

    def event_from_form(self, form: Any) -> Any:
        from ceres.character.mechanism.event_base import Event

        return Event(fulfills=self.pending_id, handler=PreCareerGraduationHandler(roll=form_int(form, 'roll', 7)))

    def input_specs(self, projection: CharacterProjection) -> list[InputSpec]:
        return [NumberEntry(name='roll', label='2D roll (2–12)', min=2, max=12)]
