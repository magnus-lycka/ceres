from ceres.character.careers.career_data import CareerData
from ceres.character.characteristics import Chars, characteristic_dm


class EntertainerCareerData(CareerData):
    def qualification_dm(self, projection) -> int:
        dex_dm = characteristic_dm(projection.summary.characteristics.get(Chars.DEX, 0))
        int_dm = characteristic_dm(projection.summary.characteristics.get(Chars.INT, 0))
        return max(dex_dm, int_dm)


CAREER_DATA_CLASS = EntertainerCareerData

EFFECT_HANDLERS: dict[str, object] = {}
SKILL_ROLL_HANDLERS: dict[str, object] = {}
CHOICE_HANDLERS: dict[str, object] = {}
