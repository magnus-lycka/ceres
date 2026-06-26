from ceres.character.domain.career.agent import AgentTerm
from ceres.character.domain.career.army import ArmyTerm
from ceres.character.domain.career.career_data import CareerTerm
from ceres.character.domain.career.citizen import CitizenTerm
from ceres.character.domain.career.drifter import DrifterTerm
from ceres.character.domain.career.entertainer import EntertainerTerm
from ceres.character.domain.career.marines import MarinesTerm
from ceres.character.domain.career.merchant import MerchantTerm
from ceres.character.domain.career.navy import NavyTerm
from ceres.character.domain.career.noble import NobleTerm
from ceres.character.domain.career.prisoner import PrisonerTerm
from ceres.character.domain.career.psion import PsionTerm
from ceres.character.domain.career.rogue import RogueTerm
from ceres.character.domain.career.scholar import ScholarTerm
from ceres.character.domain.career.scout import ScoutTerm

_all_career_term_classes: list[type[CareerTerm]] = [
    AgentTerm,
    ArmyTerm,
    CitizenTerm,
    DrifterTerm,
    EntertainerTerm,
    MarinesTerm,
    MerchantTerm,
    NavyTerm,
    NobleTerm,
    PrisonerTerm,
    PsionTerm,
    RogueTerm,
    ScholarTerm,
    ScoutTerm,
]
_CAREER_TERM_REGISTRY: dict[str, type[CareerTerm]] = {
    cls.model_fields['kind'].default: cls for cls in _all_career_term_classes
}
