from collections.abc import Mapping
from enum import StrEnum
from typing import ClassVar, Literal

from ceres.character.domain import skills as character_skills
from ceres.character.domain.career.career_data import CharCheck
from ceres.character.domain.character_state import CharacterProjection
from ceres.character.domain.characteristics import Chars
from ceres.character.domain.precareer.precareer_data import (
    PreCareerData,
    PrecareerEntryBase,
    PrecareerSkill,
    PrecareerSkillChoice,
    PreCareerTerm,
)
from ceres.character.domain.precareer.precareer_events import PendingPreCareerSkillChoice
from ceres.character.domain.skills import AnySkill, JackOfAllTrades, Leadership, Level, ProfessionSkill, skill_instances
from ceres.character.input_specs import InputSpec, NumberEntry, Select, form_int, form_str
from ceres.character.mechanism.errors import ReplayError
from ceres.character.mechanism.event_base import Event, EventHandlerBase, PendingInputBase


class ColonialUprbringingPreCareer(PreCareerData):
    name: ClassVar[str] = 'Colonial Upbringing'
    source: ClassVar[str] = 'Companion'
    entry_requirement: ClassVar[str] = 'Automatic if homeworld is TL8-'
    skill_choices: ClassVar[list[PrecareerEntryBase]] = [
        PrecareerSkill(skill=character_skills.Animals(), level=0),
        PrecareerSkill(skill=character_skills.Athletics(), level=0),
        PrecareerSkill(skill=character_skills.Drive(), level=0),
        PrecareerSkill(skill=character_skills.GunCombat(), level=0),
        PrecareerSkill(skill=character_skills.Mechanic(), level=0),
        PrecareerSkill(skill=character_skills.Medic(), level=0),
        PrecareerSkill(skill=character_skills.Navigation(), level=0),
        PrecareerSkill(skill=character_skills.Recon(), level=0),
        PrecareerSkillChoice(skills=skill_instances(ProfessionSkill), level=0),
        PrecareerSkill(skill=character_skills.Seafarer(), level=0),
        PrecareerSkill(skill=character_skills.Survival(), level=1),
    ]
    graduation: ClassVar[CharCheck] = CharCheck(characteristic=Chars.INT, target=8)
    graduation_dms: ClassVar[dict[str, int]] = {'END_8+': 1}
    honours_target: ClassVar[int] = 12
    graduation_benefits: ClassVar[list[str]] = [
        'Increase one skill already gained at level 0 to level 1',
        'Gain any two other listed skills at level 1 or increase one skill already possessed',
        'Gain Jack-of-all-Trades 1',
        'Honours graduates gain Leadership 1 and may increase another level 0 skill to level 1',
        'Increase END by +1',
        'Serve a second term and lose D3 EDU; the first career starts at 26',
    ]

    def listed_skills(self) -> list[AnySkill]:
        """The skills on the Colonial Upbringing list, every Profession skill included."""
        return [skill for entry in self.skill_choices for skill in entry.skill_options]

    def apply_graduation(
        self,
        projection: CharacterProjection,
        event: Event,
        honours: bool,
    ) -> int:
        """Companion p.32 graduation benefits, as read by RIC-033."""
        pending_idx = 0
        projection.queue_deferred(
            PendingPreCareerSkillChoice(
                pending_id=(event.id, pending_idx),
                level=1,
                still_at_0=True,
                instruction='Colonial graduation: raise one listed skill from level 0 to level 1',
                options=self.listed_skills(),
            ),
            PendingColonialGraduationPath(
                pending_id=(event.id, pending_idx + 1),
                instruction='Colonial graduation: gain two listed skills at level 1, '
                'or increase one listed skill you have by one level',
            ),
        )
        pending_idx += 2
        projection.grant_skill(JackOfAllTrades(level=Level(value=1)))
        if honours:
            projection.grant_skill(Leadership(level=Level(value=1)))
            projection.queue_deferred(
                PendingPreCareerSkillChoice(
                    pending_id=(event.id, pending_idx),
                    level=1,
                    still_at_0=True,
                    instruction='Colonial graduation (honours): raise another listed skill from level 0 to level 1',
                    options=self.listed_skills(),
                )
            )
            pending_idx += 1
        projection.summary.characteristics[Chars.END] = projection.summary.characteristics.get(Chars.END, 0) + 1
        return pending_idx

    def finish_term(
        self,
        projection: CharacterProjection,
        event: Event,
        pending_idx: int,
        *,
        graduated: bool,
        instruction: str,
    ) -> None:
        """A mandatory second term follows, graduate or not (RIC-002).

        Only a graduate loses D3 EDU in it, so only a graduate has a roll to make.
        """
        if graduated:
            projection.queue_deferred(
                PendingColonialSecondTerm(
                    pending_id=(event.id, pending_idx),
                    instruction='Second Colonial Upbringing term: roll D3 for the EDU you lose',
                )
            )
        else:
            serve_second_term(projection, event.id, pending_idx, edu_lost=0)


class ColonialUprbringingTerm(PreCareerTerm):
    kind: Literal['colonial_upbringing'] = 'colonial_upbringing'


class ColonialGraduationPath(StrEnum):
    """Colonial graduation's second benefit: one of two ways (RIC-033)."""

    TWO_SKILLS = 'two_skills'
    INCREASE = 'increase'

    @property
    def label(self) -> str:
        return {
            ColonialGraduationPath.TWO_SKILLS: 'Gain two listed skills at level 1',
            ColonialGraduationPath.INCREASE: 'Increase one listed skill you have by one level',
        }[self]


class ColonialGraduationPathHandler(EventHandlerBase):
    kind: Literal['colonial_graduation_path'] = 'colonial_graduation_path'
    path: ColonialGraduationPath

    def apply(
        self, projection: CharacterProjection, event: Event, fulfilled_pending: PendingInputBase | None = None
    ) -> None:
        upbringing = projection.summary.precareer_terms[-1].precareer
        listed = upbringing.listed_skills()
        if self.path is ColonialGraduationPath.TWO_SKILLS:
            projection.queue_immediate(
                *(
                    PendingPreCareerSkillChoice(
                        pending_id=(event.id, i),
                        level=1,
                        instruction=f'Colonial graduation: gain a listed skill at level 1 ({i + 1} of 2)',
                        options=listed,
                    )
                    for i in range(2)
                )
            )
        else:
            projection.queue_immediate(
                PendingPreCareerSkillChoice(
                    pending_id=(event.id, 0),
                    level=1,
                    increase=True,
                    instruction='Colonial graduation: increase one listed skill you have by one level',
                    options=listed,
                )
            )


class PendingColonialGraduationPath(PendingInputBase):
    kind: Literal['colonial_graduation_path'] = 'colonial_graduation_path'

    def event_from_form(self, form: Mapping[str, str]) -> Event:
        path = ColonialGraduationPath(form_str(form, 'path'))
        return Event(fulfills=self.pending_id, handler=ColonialGraduationPathHandler(path=path))

    def input_specs(self, projection: CharacterProjection) -> list[InputSpec]:
        return [
            Select(
                name='path',
                label='Second benefit',
                options=[(path.label, path.value) for path in ColonialGraduationPath],
            )
        ]


class ColonialSecondTerm(PreCareerTerm):
    """The mandatory second term of a Colonial Upbringing, with no career choice (RIC-002)."""

    kind: Literal['colonial_upbringing_second'] = 'colonial_upbringing_second'
    continues_previous: ClassVar[bool] = True


def serve_second_term(projection: CharacterProjection, event_id: int, pending_idx: int, *, edu_lost: int) -> None:
    """Four more years of colonial life, then the choice of a first career."""
    from ceres.character.domain.career.entry import queue_career_choice_indexed

    upbringing = projection.summary.precareer_terms[-1].precareer
    projection.summary.terms.append(
        ColonialSecondTerm(precareer=upbringing, start_age=projection.summary.age, completed=True)
    )
    projection.summary.age += 4
    occurrence = f'colonial_second_term_{event_id}'
    projection.start_history(
        occurrence,
        f'Term {len(projection.summary.terms)} (Colonial Upbringing): Another four years of colonial life.',
    )
    if edu_lost:
        before = projection.summary.characteristics.get(Chars.EDU, 0)
        after = max(before - edu_lost, 0)
        projection.summary.characteristics[Chars.EDU] = after
        projection.record_history(occurrence, f'EDU decreased from {before} to {after}.')
    queue_career_choice_indexed(projection, event_id, pending_idx, 'Pre-career complete — choose a career')


class ColonialSecondTermHandler(EventHandlerBase):
    kind: Literal['colonial_second_term'] = 'colonial_second_term'
    roll: int  # D3: the EDU a graduate loses in the second term

    def apply(
        self, projection: CharacterProjection, event: Event, fulfilled_pending: PendingInputBase | None = None
    ) -> None:
        if not 1 <= self.roll <= 3:
            raise ReplayError(f'A D3 roll is 1–3, not {self.roll}')
        serve_second_term(projection, event.id, 0, edu_lost=self.roll)


class PendingColonialSecondTerm(PendingInputBase):
    kind: Literal['colonial_second_term'] = 'colonial_second_term'

    def event_from_form(self, form: Mapping[str, str]) -> Event:
        return Event(fulfills=self.pending_id, handler=ColonialSecondTermHandler(roll=form_int(form, 'roll', 0)))

    def input_specs(self, projection: CharacterProjection) -> list[InputSpec]:
        return [NumberEntry(name='roll', label='D3 roll (1–3): EDU lost', min=1, max=3)]


ColonialUprbringingPreCareer.term_class = ColonialUprbringingTerm
