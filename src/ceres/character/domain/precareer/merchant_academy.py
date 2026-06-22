from typing import Any, ClassVar

from ceres.character.domain.career.career_data import CharCheck
from ceres.character.domain.career.merchant import Merchant
from ceres.character.domain.character_state import CharacterProjection
from ceres.character.domain.characteristics import Chars
from ceres.character.domain.precareer.precareer_data import PreCareerData
from ceres.character.domain.precareer.precareer_events import PendingPreCareerSkillChoice
from ceres.character.domain.psionics import Psi
from ceres.character.domain.skills import AnySkill


def _skill_instances_from_table(table) -> list[AnySkill]:
    """Return skill instances for all non-characteristic, non-list entries in a SkillTable."""
    from typing import cast as _cast

    return [_cast(AnySkill, e) for e in table.entries if not isinstance(e, (Chars, Psi, list))]


class MerchantAcademyPreCareer(PreCareerData):
    source: ClassVar[str] = 'Companion'
    entry: ClassVar[CharCheck] = CharCheck(characteristic=Chars.INT, target=9)
    entry_soc_bonus_min: ClassVar[int] = 8
    entry_soc_bonus: ClassVar[int] = 1
    graduation: ClassVar[CharCheck] = CharCheck(characteristic=Chars.INT, target=7)
    graduation_dms: ClassVar[dict[str, int]] = {'EDU_8+': 1, 'SOC_8+': 1}
    honours_target: ClassVar[int] = 11
    graduation_benefits: ClassVar[list[str]] = [
        'Increase one skill from the chosen Broker or Merchant Marine table to level 1',
        'Increase EDU by +1',
        'Automatic entry into Merchant or Citizen at rank 1 if first career and appropriate branch',
        'Honours graduates may enter those careers at rank 2',
        'DM+1 to advancement checks in Merchant or Citizen; DM+2 with honours',
    ]

    def apply_entry(
        self,
        projection: CharacterProjection,
        event: Any,
        pending_idx: int,
    ) -> int:
        merchant = Merchant()
        if self.curriculum_table:
            table = merchant.skill_table(self.curriculum_table)
            if table:
                for entry in table.entries:
                    if not isinstance(entry, (Chars, Psi, list)):
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
        event: Any,
        honours: bool,
    ) -> int:
        pending_idx = 0
        merchant = Merchant()
        skill_pool: list[AnySkill] = []
        if self.curriculum_table:
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


class MerchantAcademyBusinessPreCareer(MerchantAcademyPreCareer):
    name: ClassVar[str] = 'Merchant Academy (Business)'
    curriculum_table: ClassVar[str] = 'assignment3'


class MerchantAcademyShipboardPreCareer(MerchantAcademyPreCareer):
    name: ClassVar[str] = 'Merchant Academy (Shipboard)'
    curriculum_table: ClassVar[str] = 'assignment1'
