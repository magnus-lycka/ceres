from ceres.character.characteristics import Chars
from ceres.character.events import PendingPreCareerSkillChoice, PreCareerEntryEvent, PreCareerGraduationEvent
from ceres.character.precareers.precareer_data import PreCareerData
from ceres.character.skills import AnySkill
from ceres.character.state import CharacterProjection


def _skill_instances_from_table(table) -> list[AnySkill]:
    """Return skill instances for all non-characteristic, non-list entries in a SkillTable."""
    from typing import cast as _cast

    return [_cast(AnySkill, e) for e in table.entries if not isinstance(e, (Chars, list))]


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
            table = merchant.skill_table(self.curriculum_table)
            if table:
                for entry in table.entries:
                    if not isinstance(entry, (Chars, list)):
                        projection.grant_skill(entry)
            service_table = merchant.skill_table('service_skills')
            if service_table:
                service_skills = _skill_instances_from_table(service_table)
                projection.pending_inputs.append(
                    PendingPreCareerSkillChoice(
                        pending_id=(event.id, pending_idx),
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
        skill_pool: list[AnySkill] = []
        if merchant and self.curriculum_table:
            table = merchant.skill_table(self.curriculum_table)
            if table:
                skill_pool = _skill_instances_from_table(table)
        if skill_pool:
            projection.pending_inputs.append(
                PendingPreCareerSkillChoice(
                    pending_id=(event.id, pending_idx),
                    level=1,
                    instruction=f'{self.name} graduation: raise one curriculum skill to level 1',
                    options=skill_pool,
                )
            )
            pending_idx += 1
        projection.summary.characteristics[Chars.EDU] = projection.summary.characteristics.get(Chars.EDU, 0) + 1
        adv_dm = 2 if honours else 1
        rank_entry = 2 if honours else 1
        projection.summary.problems.append(
            f'{self.name} graduation: may enter Merchant (correct branch) or Citizen automatically at rank {rank_entry}'
            ' if this is the first career entered after the academy. Apply manually.'
        )
        projection.summary.problems.append(
            f'{self.name} graduation: DM+{adv_dm} on all advancement checks in Merchant or Citizen. Apply manually.'
        )
        return pending_idx
