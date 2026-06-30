from typing import ClassVar, Literal

from ceres.character.domain.career.army import Army
from ceres.character.domain.career.career_data import CareerData, CharCheck
from ceres.character.domain.career.marines import Marines
from ceres.character.domain.career.navy import Navy
from ceres.character.domain.character_state import CharacterProjection
from ceres.character.domain.characteristics import Chars
from ceres.character.domain.precareer.precareer_data import PreCareerData, PreCareerTerm
from ceres.character.domain.psionics_data import Psi
from ceres.character.mechanism.event_base import Event


class MilitaryAcademyPreCareer(PreCareerData):
    source: ClassVar[str] = 'Core'
    entry_term_dms: ClassVar[dict[int, int]] = {2: -2, 3: -4}
    service_skills_from: ClassVar[type[CareerData]]
    tied_career: ClassVar[str]
    graduation: ClassVar[CharCheck] = CharCheck(characteristic=Chars.INT, target=7)
    graduation_dms: ClassVar[dict[str, int]] = {'END_8+': 1, 'SOC_8+': 1}
    honours_target: ClassVar[int] = 11
    graduation_benefits: ClassVar[list[str]] = [
        'If entering the tied military career, select any three Service Skills and increase them to level 1',
        'Increase EDU by +1',
        'If graduating with honours, increase SOC by +1',
        'Automatic entry into the tied military career if it is first attempted after graduation',
        'Commission roll before first term of a military career, with DM+2; honours makes it automatic',
    ]

    def apply_entry(
        self,
        projection: CharacterProjection,
        event: Event,
        pending_idx: int,
    ) -> int:
        service_table = self.service_skills_from().skill_table('service_skills')
        if service_table:
            for entry in service_table.entries:
                if not isinstance(entry, (Chars, Psi, list)):
                    projection.grant_skill(entry)
        return pending_idx

    def apply_graduation(
        self,
        projection: CharacterProjection,
        event: Event,
        honours: bool,
    ) -> int:
        projection.summary.characteristics[Chars.EDU] = projection.summary.characteristics.get(Chars.EDU, 0) + 1
        if honours:
            projection.summary.characteristics[Chars.SOC] = projection.summary.characteristics.get(Chars.SOC, 0) + 1
        career_name = self.service_skills_from.name
        projection.auto_qualify_careers.append(self.service_skills_from)
        projection.summary.problems.append(
            f'{self.name} graduation: if entering {career_name}, '
            'select any three Service Skills and increase them to level 1. Apply manually.'
        )
        projection.summary.problems.append(
            f'{self.name} graduation: entitled to a commission roll at the start of '
            f'your first {career_name} career term with DM+2'
            + (' (automatic with honours).' if honours else '.')
            + ' Apply manually.'
        )
        return 0

    def apply_failed_graduation(
        self,
        projection: CharacterProjection,
        event: Event,
    ) -> None:
        if event.roll > 2:
            projection.auto_qualify_careers.append(self.service_skills_from)
            projection.summary.problems.append(
                f'{self.name}: failed graduation (roll > 2) — may still enter '
                f'{self.service_skills_from.name} automatically, but no commission roll in first term.'
            )


class ArmyAcademyPreCareer(MilitaryAcademyPreCareer):
    name: ClassVar[str] = 'Army Academy'
    entry: ClassVar[CharCheck] = CharCheck(characteristic=Chars.END, target=7)
    service_skills_from: ClassVar[type[CareerData]] = Army
    tied_career: ClassVar[str] = Army.name


class MarineAcademyPreCareer(MilitaryAcademyPreCareer):
    name: ClassVar[str] = 'Marine Academy'
    entry: ClassVar[CharCheck] = CharCheck(characteristic=Chars.END, target=8)
    service_skills_from: ClassVar[type[CareerData]] = Marines
    tied_career: ClassVar[str] = Marines.name


class NavyAcademyPreCareer(MilitaryAcademyPreCareer):
    name: ClassVar[str] = 'Navy Academy'
    entry: ClassVar[CharCheck] = CharCheck(characteristic=Chars.INT, target=8)
    service_skills_from: ClassVar[type[CareerData]] = Navy
    tied_career: ClassVar[str] = Navy.name


class ArmyAcademyTerm(PreCareerTerm):
    kind: Literal['army_academy'] = 'army_academy'


class MarineAcademyTerm(PreCareerTerm):
    kind: Literal['marine_academy'] = 'marine_academy'


class NavyAcademyTerm(PreCareerTerm):
    kind: Literal['navy_academy'] = 'navy_academy'


ArmyAcademyPreCareer.term_class = ArmyAcademyTerm
MarineAcademyPreCareer.term_class = MarineAcademyTerm
NavyAcademyPreCareer.term_class = NavyAcademyTerm
