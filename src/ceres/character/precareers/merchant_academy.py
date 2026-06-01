from ceres.character.characteristics import Chars
from ceres.character.events import PendingPreCareerSkillChoice, PreCareerEntryEvent, PreCareerGraduationEvent
from ceres.character.precareers.precareer_data import PreCareerData
from ceres.character.skills import skill_from_str
from ceres.character.state import (
    CharacterProjection,
    ScheduledEffect,
)


class MerchantAcademyPreCareer(PreCareerData):
    def apply_entry(
        self,
        projection: CharacterProjection,
        event: PreCareerEntryEvent,
        pending_idx: int,
    ) -> int:
        from ceres.character.careers.loader import load_careers

        merchant = load_careers().get('Merchant')
        if merchant and self.curriculum_table:
            table = merchant.skill_tables.get(self.curriculum_table)
            if table:
                for entry in table.entries.values():
                    if entry.skill:
                        projection.grant_skill(skill_from_str(entry.skill, 0))
            service_table = merchant.skill_tables.get('service_skills')
            if service_table:
                service_skills = [e.skill for e in service_table.entries.values() if e.skill]
                projection.pending_inputs.append(
                    PendingPreCareerSkillChoice(
                        id=f'{event.id}.{pending_idx}',
                        level=1,
                        instruction=f'{self.name}: choose one Service Skill at level 1',
                        options=service_skills,
                    )
                )
                pending_idx += 1
        return pending_idx

    def apply_graduation(
        self,
        projection: CharacterProjection,
        event: PreCareerGraduationEvent,
        honours: bool,
    ) -> int:
        from ceres.character.careers.loader import load_careers

        pending_idx = 0
        merchant = load_careers().get('Merchant')
        skill_pool: list[str] = []
        if merchant and self.curriculum_table:
            table = merchant.skill_tables.get(self.curriculum_table)
            if table:
                skill_pool = [e.skill for e in table.entries.values() if e.skill]
        if skill_pool:
            projection.pending_inputs.append(
                PendingPreCareerSkillChoice(
                    id=f'{event.id}.{pending_idx}',
                    level=1,
                    instruction=f'{self.name} graduation: raise one curriculum skill to level 1',
                    options=skill_pool,
                )
            )
            pending_idx += 1
        projection.summary.characteristics[Chars.EDU] = projection.summary.characteristics.get(Chars.EDU, 0) + 1
        adv_dm = 2 if honours else 1
        projection.scheduled_effects.append(
            ScheduledEffect(
                trigger='advancement',
                source_event_id=event.id,
                effect={'type': 'dm', 'amount': adv_dm},
                consume=False,
            )
        )
        rank_entry = 2 if honours else 1
        projection.summary.problems.append(
            f'{self.name} graduation: may enter Merchant (correct branch) or Citizen automatically at rank {rank_entry}'
            ' if this is the first career entered after the academy. Apply manually.'
        )
        projection.summary.problems.append(
            f'{self.name} graduation: DM+{adv_dm} on all advancement checks in Merchant or Citizen. Apply manually.'
        )
        return pending_idx
