from ceres.character.careers.career_data import CareerData, CareerDispatchEffect
from ceres.character.characteristics import Chars, characteristic_dm
from ceres.character.events import SkillRollEvent
from ceres.character.projection import (
    CharacterProjection,
    Enemy,
    PendingCareerEvent,
    PendingCareerSkillRoll,
    ScheduledEffect,
)


class EntertainerCareerData(CareerData):
    def qualification_dm(self, projection) -> int:
        dex_dm = characteristic_dm(projection.summary.characteristics.get(Chars.DEX, 0))
        int_dm = characteristic_dm(projection.summary.characteristics.get(Chars.INT, 0))
        return max(dex_dm, int_dm)


# ── event 3: controversial exhibition ────────────────────────────────────────


def _handle_entertainer_event_3(
    projection: CharacterProjection,
    effect: CareerDispatchEffect,
    event_id: int,
    pending_idx: int,
) -> int:
    projection.pending_inputs.append(
        PendingCareerSkillRoll(
            id=f'{event_id}.{pending_idx}',
            career='Entertainer',
            roll=3,
            context='entertainer_event_3',
            instruction='Roll Art or Investigate 8+: success = SOC +1; fail = SOC -1',
            options=['Art', 'Investigate'],
        )
    )
    return pending_idx + 1


def _resolve_entertainer_event_3(projection: CharacterProjection, event: SkillRollEvent) -> None:
    if event.modified_roll >= 8:
        projection.summary.characteristics[Chars.SOC] = projection.summary.characteristics.get(Chars.SOC, 0) + 1
    else:
        projection.summary.characteristics[Chars.SOC] = max(0, projection.summary.characteristics.get(Chars.SOC, 0) - 1)
    # no pending added — _apply_skill_roll auto-queues advancement


# ── event 8: criticise political leader ──────────────────────────────────────


def _handle_entertainer_event_8(
    projection: CharacterProjection,
    effect: CareerDispatchEffect,
    event_id: int,
    pending_idx: int,
) -> int:
    projection.pending_inputs.append(
        PendingCareerEvent(
            id=f'{event_id}.{pending_idx}',
            career='Entertainer',
            roll=8,
            instruction=(
                'Criticise the political leader (roll Art or Investigate 8+: '
                'success = DM+2 to next advancement, fail = gain powerful Enemy) or refuse?'
            ),
            options=['accept', 'refuse'],
        )
    )
    return pending_idx + 1


def _choice_entertainer_event_8(projection: CharacterProjection, event) -> None:
    career = projection.get_current_career()
    if event.choice == 'refuse':
        projection.pending_inputs.append(projection.career_progress_pending(career, event.id))
    else:
        projection.pending_inputs.append(
            PendingCareerSkillRoll(
                id=f'{event.id}.0',
                career='Entertainer',
                roll=8,
                context='entertainer_event_8_skill',
                instruction=(
                    'Roll Art or Investigate 8+: success = DM+2 to next advancement; fail = gain powerful Enemy'
                ),
                options=['Art', 'Investigate'],
            )
        )


def _resolve_entertainer_event_8_skill(projection: CharacterProjection, event: SkillRollEvent) -> None:
    if event.modified_roll >= 8:
        projection.scheduled_effects.append(
            ScheduledEffect(
                trigger='advancement',
                source_event_id=event.id,
                effect={'type': 'dm', 'amount': 2},
            )
        )
    else:
        projection.summary.connections.append(Enemy(source='Powerful politician (Entertainer event 8)'))
    # no pending added — _apply_skill_roll auto-queues advancement


# ── handler registries ────────────────────────────────────────────────────────

CAREER_DATA_CLASS = EntertainerCareerData

EFFECT_HANDLERS: dict[str, object] = {
    'entertainer_event_3': _handle_entertainer_event_3,
    'entertainer_event_8': _handle_entertainer_event_8,
}

SKILL_ROLL_HANDLERS: dict[str, object] = {
    'entertainer_event_3': _resolve_entertainer_event_3,
    'entertainer_event_8_skill': _resolve_entertainer_event_8_skill,
}

CHOICE_HANDLERS: dict[str, object] = {
    'entertainer_event_8': _choice_entertainer_event_8,
}
