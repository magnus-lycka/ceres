from typing import ClassVar

from ceres.character.domain.career.career_data import CharCheck
from ceres.character.domain.career.psion import Psion
from ceres.character.domain.character_state import CharacterProjection, CharacterSummary
from ceres.character.domain.characteristics import Chars, ConnectionKind
from ceres.character.domain.precareer.precareer_data import PreCareerData, PrecareerSkillEntry
from ceres.character.domain.psionics import PendingPsionicTalentLevelChoice, queue_psionic_institute_training
from ceres.character.domain.skills import Level, LifeScience, ProfessionSkill, ScienceSkill, Streetwise, skill_instances
from ceres.character.mechanism.event_base import Event


class PsionicCommunityPreCareer(PreCareerData):
    name: ClassVar[str] = 'Psionic Community'
    source: ClassVar[str] = 'Companion'
    entry: ClassVar[CharCheck] = CharCheck(characteristic=Chars.PSI, target=8)
    entry_requirement: ClassVar[str] = 'PSI 8+, DM+1 if INT 8+'
    entry_dms: ClassVar[dict[str, int]] = {'INT_8+': 1}
    skill_choices: ClassVar[list[PrecareerSkillEntry]] = [
        PrecareerSkillEntry(skill=skill_instances(ProfessionSkill), level=0),
        PrecareerSkillEntry(skill=skill_instances(ScienceSkill), level=0),
        PrecareerSkillEntry(skill=Streetwise(), level=0),
    ]
    graduation: ClassVar[CharCheck] = CharCheck(characteristic=Chars.PSI, target=6)
    graduation_requirement: ClassVar[str] = 'PSI 6+, DM+1 if INT 8+'
    graduation_dms: ClassVar[dict[str, int]] = {'INT_8+': 1}
    honours_target: ClassVar[int] = 12
    graduation_benefits: ClassVar[list[str]] = [
        'Increase PSI by +1',
        'Skill level 1 in any one talent possessed',
        'Science (psionicology) 1',
        'Honours graduates gain all acquired talents at level 1 and may advance one to level 2',
        'Automatic enlistment in Psion career, even after intervening careers',
        'Gain a Rival, or an Enemy with honours',
    ]

    def is_available(self, summary: CharacterSummary) -> bool:
        return summary.psionics is not None

    def apply_entry(self, projection: CharacterProjection, event: Event, pending_idx: int) -> int:
        pending_idx = super().apply_entry(projection, event, pending_idx)
        if queue_psionic_institute_training(projection, event.id, pending_idx):
            pending_idx += 1
        return pending_idx

    def apply_graduation(
        self,
        projection: CharacterProjection,
        event: Event,
        honours: bool,
    ) -> int:

        pending_idx = 0
        if projection.summary.psionics is None:
            raise ValueError('Psionic Community graduation requires Psionic Strength')
        projection.summary.characteristics[Chars.PSI] = projection.summary.characteristics.get(Chars.PSI, 0) + 1
        psionics = projection.summary.psionics
        if honours:
            for talent in psionics.psionic_talent_skills:
                psionics.raise_talent_to(type(talent), 1)
            target_level = 2
        else:
            target_level = 1
        if any(talent.level.value < target_level for talent in psionics.psionic_talent_skills):
            projection.pending_inputs.append(
                PendingPsionicTalentLevelChoice(
                    pending_id=(event.id, pending_idx),
                    level=target_level,
                    instruction=f'Psionic Community graduation: choose one possessed talent at level {target_level}',
                )
            )
            pending_idx += 1
        projection.grant_skill(LifeScience(psionicology=Level(value=1)))
        if Psion not in projection.auto_qualify_careers:
            projection.auto_qualify_careers.append(Psion)
        source = 'Psionic Community graduation'
        if honours:
            projection.add_connection(ConnectionKind.ENEMY, origin=source)
        else:
            projection.add_connection(ConnectionKind.RIVAL, origin=source)
        return pending_idx
