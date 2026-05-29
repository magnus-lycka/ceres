from ceres.character.careers.career_data import AssignmentData, CareerData


class PrisonerCareerData(CareerData):
    def start_career(
        self,
        projection,
        assignment: AssignmentData,
        event_id: int,
        qualification_roll: int,
    ) -> None:
        projection.summary.current_career = self.name
        projection.summary.current_assignment = assignment.name
        self.start_new_term(projection, assignment, event_id)


CAREER_DATA_CLASS = PrisonerCareerData

EFFECT_HANDLERS: dict[str, object] = {}
SKILL_ROLL_HANDLERS: dict[str, object] = {}
CHOICE_HANDLERS: dict[str, object] = {}
