"""Shared helpers for career event and mishap handlers."""

from typing import Literal

from ceres.character.domain.career.career_data import CareerHandlerBase
from ceres.character.domain.career.career_events import PendingChoices, _apply_mishap_ejection
from ceres.character.domain.career.common_pending import PendingAdvancedTrainingSkillRoll
from ceres.character.domain.character_state import CharacterProjection
from ceres.character.domain.characteristics import Chars
from ceres.character.domain.health.health_events import PendingDoubleInjuryRoll
from ceres.character.mechanism.pending_input import ChoiceBase


def handle_advanced_training(
    projection: CharacterProjection,
    event_id: int,
    pending_idx: int,
    threshold: int = 8,
) -> int:
    instruction = f'Roll EDU {threshold}+ to increase any one skill you already have by one level'
    projection.pending_inputs.append(
        PendingAdvancedTrainingSkillRoll(
            pending_id=(event_id, pending_idx),
            instruction=instruction,
            options=[Chars.EDU],
            threshold=threshold,
        )
    )
    return pending_idx + 1


class CommonMishap1Severe(ChoiceBase):
    kind: Literal['common_mishap_1_severe'] = 'common_mishap_1_severe'
    label: str = 'Severely injured (same as result 2 on Injury table: choose a physical characteristic to reduce by 2)'

    def handle(self, projection: CharacterProjection, event) -> None:
        from ceres.character.domain.health.health_events import PendingCharacteristicChoice

        career = projection.get_current_career()
        projection.pending_inputs.append(
            PendingCharacteristicChoice(
                pending_id=(event.id, 0),
                instruction='Severely injured: choose STR, DEX, or END to reduce by 2',
                options=[Chars.STR, Chars.DEX, Chars.END],
                amount=2,
            )
        )
        _apply_mishap_ejection(projection, career, event.id, 1, lose_current_term=True)


class CommonMishap1DoubleRoll(ChoiceBase):
    kind: Literal['common_mishap_1_double_roll'] = 'common_mishap_1_double_roll'
    label: str = 'Roll twice on Injury table and take the lower result'

    def handle(self, projection: CharacterProjection, event) -> None:
        career = projection.get_current_career()
        projection.pending_inputs.append(
            PendingDoubleInjuryRoll(
                pending_id=(event.id, 0),
                instruction='Roll twice on the Injury table and apply the lower result',
            )
        )
        _apply_mishap_ejection(projection, career, event.id, 1, lose_current_term=True)


class CommonMishap1Handler(CareerHandlerBase):
    type: Literal['common_mishap_1'] = 'common_mishap_1'

    @staticmethod
    def handle(projection: CharacterProjection, event_id: int, pending_idx: int) -> int:
        projection.pending_inputs.append(
            PendingChoices(
                pending_id=(event_id, pending_idx),
                instruction=(
                    'Severely injured: take severe injury (reduce a physical characteristic by 2) '
                    'or roll twice on the Injury table and take the lower result?'
                ),
                choices=[CommonMishap1Severe(), CommonMishap1DoubleRoll()],
            )
        )
        return pending_idx + 1
