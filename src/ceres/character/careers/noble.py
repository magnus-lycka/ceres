from ceres.character.careers.career_data import CareerData


class NobleCareerData(CareerData):
    pass


CAREER_DATA_CLASS = NobleCareerData

EFFECT_HANDLERS: dict[str, object] = {}
SKILL_ROLL_HANDLERS: dict[str, object] = {}
CHOICE_HANDLERS: dict[str, object] = {}
