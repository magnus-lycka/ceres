from ceres.character.characteristics import Chars
from ceres.character.events import PreCareerEntryEvent, PreCareerGraduationEvent
from ceres.character.precareers.precareer_data import PreCareerData
from ceres.character.skills import skill_from_str
from ceres.character.state import (
    CharacterProjection,
    ScheduledEffect,
)


class MilitaryAcademyPreCareer(PreCareerData):
    def apply_entry(
        self,
        projection: CharacterProjection,
        event: PreCareerEntryEvent,
        pending_idx: int,
    ) -> int:
        from ceres.character.careers.loader import load_careers

        tied_career = load_careers().get(self.service_skills_from or '')
        if tied_career:
            service_table = tied_career.skill_tables.get('service_skills')
            if service_table:
                for entry in service_table.entries.values():
                    if entry.skill:
                        projection.grant_skill(skill_from_str(entry.skill, 0))
        return pending_idx

    def apply_graduation(
        self,
        projection: CharacterProjection,
        event: PreCareerGraduationEvent,
        honours: bool,
    ) -> int:
        projection.summary.characteristics[Chars.EDU] = projection.summary.characteristics.get(Chars.EDU, 0) + 1
        if honours:
            projection.summary.characteristics[Chars.SOC] = projection.summary.characteristics.get(Chars.SOC, 0) + 1
        projection.scheduled_effects.append(
            ScheduledEffect(
                trigger='auto_qualify',
                source_event_id=event.id,
                effect={'career': self.service_skills_from},
                consume=True,
            )
        )
        projection.summary.problems.append(
            f'{self.name} graduation: if entering {self.service_skills_from}, '
            'select any three Service Skills and increase them to level 1. Apply manually.'
        )
        projection.summary.problems.append(
            f'{self.name} graduation: entitled to a commission roll at the start of '
            f'your first {self.service_skills_from} career term with DM+2'
            + (' (automatic with honours).' if honours else '.')
            + ' Apply manually.'
        )
        return 0

    def apply_failed_graduation(
        self,
        projection: CharacterProjection,
        event: PreCareerGraduationEvent,
    ) -> None:
        if event.roll > 2:
            projection.scheduled_effects.append(
                ScheduledEffect(
                    trigger='auto_qualify',
                    source_event_id=event.id,
                    effect={'career': self.service_skills_from, 'no_commission': True},
                    consume=True,
                )
            )
            projection.summary.problems.append(
                f'{self.name}: failed graduation (roll > 2) — may still enter '
                f'{self.service_skills_from} automatically, but no commission roll in first term.'
            )
