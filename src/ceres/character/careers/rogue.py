from ceres.character.careers.career_data import CareerData


class RogueCareerData(CareerData):
    pass


CAREER_DATA_CLASS = RogueCareerData

EFFECT_HANDLERS: dict[str, object] = {}
SKILL_ROLL_HANDLERS: dict[str, object] = {}
CHOICE_HANDLERS: dict[str, object] = {}
