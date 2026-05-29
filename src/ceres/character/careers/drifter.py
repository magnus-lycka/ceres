from ceres.character.careers.career_data import CareerData


class DrifterCareerData(CareerData):
    def _basic_training_table_name(self, assignment) -> str:
        return assignment.name.lower()


CAREER_DATA_CLASS = DrifterCareerData

EFFECT_HANDLERS: dict[str, object] = {}
SKILL_ROLL_HANDLERS: dict[str, object] = {}
CHOICE_HANDLERS: dict[str, object] = {}
