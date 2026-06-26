from ceres.character.domain.precareer.colonial_upbringing import ColonialUprbringingTerm
from ceres.character.domain.precareer.merchant_academy import MerchantAcademyBusinessTerm, MerchantAcademyShipboardTerm
from ceres.character.domain.precareer.military_academy import ArmyAcademyTerm, MarineAcademyTerm, NavyAcademyTerm
from ceres.character.domain.precareer.precareer_data import PreCareerTerm
from ceres.character.domain.precareer.psionic_community import PsionicCommunityTerm
from ceres.character.domain.precareer.school_of_hard_knocks import SchoolOfHardKnocksTerm
from ceres.character.domain.precareer.spacer_community import SpacerCommunityTerm
from ceres.character.domain.precareer.university import UniversityTerm

__all__ = [
    'ArmyAcademyTerm',
    'ColonialUprbringingTerm',
    'MarineAcademyTerm',
    'MerchantAcademyBusinessTerm',
    'MerchantAcademyShipboardTerm',
    'NavyAcademyTerm',
    'PreCareerTerm',
    'PsionicCommunityTerm',
    'SchoolOfHardKnocksTerm',
    'SpacerCommunityTerm',
    'UniversityTerm',
]

_all_precareer_term_classes: list[type[PreCareerTerm]] = [
    UniversityTerm,
    ArmyAcademyTerm,
    MarineAcademyTerm,
    NavyAcademyTerm,
    ColonialUprbringingTerm,
    MerchantAcademyBusinessTerm,
    MerchantAcademyShipboardTerm,
    PsionicCommunityTerm,
    SchoolOfHardKnocksTerm,
    SpacerCommunityTerm,
]
_PRECAREER_TERM_REGISTRY: dict[str, type[PreCareerTerm]] = {
    cls.model_fields['kind'].default: cls for cls in _all_precareer_term_classes
}
