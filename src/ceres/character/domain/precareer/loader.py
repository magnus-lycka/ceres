from collections.abc import Iterable
from functools import cache

from ceres.character.domain.precareer.colonial_upbringing import ColonialUprbringingPreCareer
from ceres.character.domain.precareer.merchant_academy import (
    MerchantAcademyBusinessPreCareer,
    MerchantAcademyShipboardPreCareer,
)
from ceres.character.domain.precareer.military_academy import (
    ArmyAcademyPreCareer,
    MarineAcademyPreCareer,
    NavyAcademyPreCareer,
)
from ceres.character.domain.precareer.precareer_data import PreCareerData
from ceres.character.domain.precareer.psionic_community import PsionicCommunityPreCareer
from ceres.character.domain.precareer.school_of_hard_knocks import SchoolOfHardKnocksPreCareer
from ceres.character.domain.precareer.spacer_community import SpacerCommunityPreCareer
from ceres.character.domain.precareer.university import UniversityPreCareer


@cache
def load_precareers() -> tuple[PreCareerData, ...]:
    return (
        UniversityPreCareer(),
        ArmyAcademyPreCareer(),
        MarineAcademyPreCareer(),
        NavyAcademyPreCareer(),
        ColonialUprbringingPreCareer(),
        MerchantAcademyBusinessPreCareer(),
        MerchantAcademyShipboardPreCareer(),
        PsionicCommunityPreCareer(),
        SchoolOfHardKnocksPreCareer(),
        SpacerCommunityPreCareer(),
    )


def precareer_from_user_input_name(
    name: str,
    precareers: Iterable[PreCareerData] | None = None,
) -> PreCareerData | None:
    """Resolve a pre-career name received from a UI/form boundary."""
    return next((precareer for precareer in precareers or load_precareers() if precareer.name == name), None)


def precareer_of_type[PreCareerT: PreCareerData](precareer_type: type[PreCareerT]) -> PreCareerT:
    """Return the loaded pre-career instance for a concrete PreCareerData subclass."""
    precareer = next((precareer for precareer in load_precareers() if isinstance(precareer, precareer_type)), None)
    if precareer is None:
        raise LookupError(f'Pre-career type is not loaded: {precareer_type!r}')
    return precareer
