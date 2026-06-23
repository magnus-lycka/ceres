from collections.abc import Mapping
from typing import Literal

from pydantic import Field

from ceres.character.domain.career.career_data import CareerData
from ceres.character.domain.character_state import CharacterProjection
from ceres.character.domain.characteristics import ConnectionKind
from ceres.character.domain.psionics import PendingLifeEventPsionicsRoll
from ceres.character.domain.skills import AnySkill, SpaceScience
from ceres.character.input_specs import InputSpec, NumberEntry, Select, form_int, form_str, literal
from ceres.character.mechanism.errors import ReplayError
from ceres.character.mechanism.event_base import Event, EventHandlerBase
from ceres.character.mechanism.pending_input import ChoiceBase, PendingInputBase


def _queue_advancement(
    projection: CharacterProjection, career: CareerData, event_id: int, pending_idx: int = 0
) -> None:
    from ceres.character.domain.career.advancement import advancement_pending

    projection.pending_inputs.append(
        advancement_pending(career, projection.summary.current_assignment, event_id, pending_idx)
    )


class ConnectionKindChoiceHandler(EventHandlerBase):
    kind: Literal['connection_kind_choice'] = 'connection_kind_choice'
    connection_kind: ConnectionKind

    def apply(
        self, projection: CharacterProjection, event: Event, fulfilled_pending: PendingInputBase | None = None
    ) -> None:

        if isinstance(fulfilled_pending, PendingLifeEventChoice):
            source = f'Life event roll {fulfilled_pending.roll}'
        else:
            source = 'unknown'
        projection.add_connection(self.connection_kind, origin=f'Life event: {source}')
        narratives = {
            4: {
                ConnectionKind.RIVAL: 'Life event: relationship ended, gained a rival',
                ConnectionKind.ENEMY: 'Life event: relationship ended, gained an enemy',
            },
            8: {
                ConnectionKind.RIVAL: 'Life event: betrayal, gained a rival',
                ConnectionKind.ENEMY: 'Life event: betrayal, gained an enemy',
            },
        }
        if isinstance(fulfilled_pending, PendingLifeEventChoice) and (
            narrative := narratives.get(fulfilled_pending.roll, {}).get(self.connection_kind)
        ):
            projection.summary.narrative.append(narrative)


class LifeEventHandler(EventHandlerBase):
    kind: Literal['life_event'] = 'life_event'
    roll: int

    def apply(
        self, projection: CharacterProjection, event: Event, fulfilled_pending: PendingInputBase | None = None
    ) -> None:
        from ceres.character.domain.career.career_data import BenefitRollDm
        from ceres.character.domain.career.career_events import PendingChoices
        from ceres.character.domain.connection import Ally, Contact
        from ceres.character.domain.health.health_events import PendingInjuryTable
        from ceres.character.domain.homeworld.homeworld_events import PendingHomeworldChangeRequired

        if not (2 <= self.roll <= 12):
            raise ReplayError(f'Life event roll must be 2-12, got {self.roll}')
        career = projection.get_current_career() if projection.summary.current_career is not None else None
        narratives = {
            2: 'Life event: sickness or injury',
            3: 'Life event: birth or death in the family',
            4: 'Life event: ending of a relationship',
            5: 'Life event: relationship strengthened (ally gained)',
            6: 'Life event: new relationship (ally gained)',
            7: 'Life event: new contact made',
            9: 'Life event: travel (qualification DM ahead)',
            10: 'Life event: good fortune (benefit roll bonus)',
            11: 'Life event: crime (lost a benefit roll)',
            12: 'Life event: unusual event — see sub-table',
        }
        if narrative := narratives.get(self.roll):
            projection.summary.narrative.append(narrative)
        match self.roll:
            case 2:
                projection.pending_inputs.append(
                    PendingInjuryTable(
                        pending_id=(event.id, 0),
                        instruction='Roll 1D on Injury table (sickness/injury)',
                    )
                )
                if career is not None:
                    _queue_advancement(projection, career, event.id, 1)
            case 3:
                if career is not None:
                    _queue_advancement(projection, career, event.id)
            case 4:
                projection.pending_inputs.append(
                    PendingLifeEventChoice(
                        pending_id=(event.id, 0),
                        roll=4,
                        instruction='Ending relationship: gain a rival or enemy?',
                        options=[ConnectionKind.RIVAL, ConnectionKind.ENEMY],
                    )
                )
                if career is not None:
                    _queue_advancement(projection, career, event.id, 1)
            case 5 | 6:
                source = 'Life event: improved relationship' if self.roll == 5 else 'Life event: new relationship'
                projection.add_connection(ConnectionKind.ALLY, origin=source)
                if career is not None:
                    _queue_advancement(projection, career, event.id)
            case 7:
                projection.add_connection(ConnectionKind.CONTACT, origin='Life event: new contact')
                if career is not None:
                    _queue_advancement(projection, career, event.id)
            case 8:
                convertible = [
                    connection
                    for connection in projection.summary.connections
                    if isinstance(connection, (Contact, Ally))
                ]
                if convertible:
                    projection.pending_inputs.append(
                        PendingLifeEventBetrayalConvert(
                            pending_id=(event.id, 0),
                            instruction='Betrayal: choose a Contact or Ally to convert to a Rival or Enemy',
                        )
                    )
                else:
                    projection.pending_inputs.append(
                        PendingLifeEventChoice(
                            pending_id=(event.id, 0),
                            roll=8,
                            instruction='Betrayal: no contacts or allies — gain a rival or enemy?',
                            options=[ConnectionKind.RIVAL, ConnectionKind.ENEMY],
                        )
                    )
                if career is not None:
                    _queue_advancement(projection, career, event.id, 1)
            case 9:
                projection.pending_qualification_dm += 2
                projection.pending_inputs.append(
                    PendingHomeworldChangeRequired(
                        pending_id=(event.id, 0),
                        instruction='You move to another world. Select your new homeworld.',
                        reason='Life Event 9: You move to another world.',
                        source_kind='life_event_move',
                    )
                )
                if career is not None:
                    _queue_advancement(projection, career, event.id, 1)
            case 10:
                if projection.summary.career_terms:
                    projection.summary.career_terms[-1].require_muster_out().benefit_roll_dms.append(
                        BenefitRollDm(amount=2)
                    )
                if career is not None:
                    _queue_advancement(projection, career, event.id)
            case 11:
                projection.pending_inputs.append(
                    PendingChoices(
                        pending_id=(event.id, 0),
                        instruction='Crime: choose a consequence',
                        choices=[LifeEventCrimeLoseBenefitRoll(), LifeEventCrimeTakePrisoner()],
                    )
                )
                if career is not None:
                    _queue_advancement(projection, career, event.id, 1)
            case 12:
                projection.pending_inputs.append(PendingLifeEventUnusual(pending_id=(event.id, 0)))


class LifeEventUnusualHandler(EventHandlerBase):
    kind: Literal['life_event_unusual'] = 'life_event_unusual'
    roll: int

    def apply(
        self, projection: CharacterProjection, event: Event, fulfilled_pending: PendingInputBase | None = None
    ) -> None:

        if not (1 <= self.roll <= 6):
            raise ReplayError(f'Life event unusual roll must be 1-6, got {self.roll}')
        career = projection.get_current_career() if projection.summary.current_career is not None else None
        if self.roll == 1:
            projection.summary.narrative.append('Unusual event: psionic experience — may test Psionic Strength')
            projection.pending_inputs.append(
                PendingLifeEventPsionicsRoll(pending_id=(event.id, 0), instruction='Roll 2D for Psionic Strength test')
            )
            if career is not None:
                _queue_advancement(projection, career, event.id, 1)
        elif self.roll == 2:
            projection.add_connection(ConnectionKind.CONTACT, origin='Unusual event: alien contact')
            projection.summary.narrative.append('Unusual event: alien encounter — gained contact and a science skill')
            projection.pending_inputs.append(
                PendingLifeEventAlienScience(
                    pending_id=(event.id, 0),
                    instruction='Choose a science skill gained from alien encounter',
                )
            )
            if career is not None:
                _queue_advancement(projection, career, event.id, 1)
        else:
            narrative = {
                3: 'Unusual event: alien artefact found',
                4: 'Unusual event: amnesia',
                5: 'Unusual event: contacted by shadowy government agency',
                6: 'Unusual event: encountered Ancient technology',
            }[self.roll]
            projection.summary.narrative.append(narrative)
            if career is not None:
                _queue_advancement(projection, career, event.id)


class BetrayalConvertHandler(EventHandlerBase):
    kind: Literal['betrayal_convert'] = 'betrayal_convert'
    connection_index: int
    new_kind: ConnectionKind

    def apply(
        self, projection: CharacterProjection, event: Event, fulfilled_pending: PendingInputBase | None = None
    ) -> None:
        from ceres.character.domain.connection import make_connection

        if self.connection_index >= len(projection.summary.connections):
            raise ReplayError(f'Connection index {self.connection_index} out of range')
        old = projection.summary.connections[self.connection_index]
        projection.summary.connections[self.connection_index] = make_connection(
            self.new_kind,
            origin=f'Betrayal: {old.origin}',
        )


class LifeEventCrimeLoseBenefitRoll(ChoiceBase):
    kind: Literal['life_event_crime_lose_benefit_roll'] = 'life_event_crime_lose_benefit_roll'
    label: str = 'Lose one Benefit roll'

    def handle(self, projection: CharacterProjection, event: Event) -> None:
        if projection.summary.career_terms:
            projection.summary.career_terms[-1].require_muster_out().lost_rolls += 1


class LifeEventCrimeTakePrisoner(ChoiceBase):
    kind: Literal['life_event_crime_take_prisoner'] = 'life_event_crime_take_prisoner'
    label: str = 'Take the Prisoner career next term'

    def handle(self, projection: CharacterProjection, event: Event) -> None:
        from ceres.character.domain.career.prisoner import PRISONER

        projection.forced_next_career = PRISONER
        if projection.summary.career_terms:
            projection.summary.career_terms[
                -1
            ].prison = 'Crime life event — chose to take the Prisoner career next term.'


class PendingLifeEvent(PendingInputBase):
    kind: Literal['life_event'] = 'life_event'

    def event_from_form(self, form: Mapping[str, str]) -> Event:
        return Event(fulfills=self.pending_id, handler=LifeEventHandler(roll=form_int(form, 'roll', 2)))

    def input_specs(self, projection: CharacterProjection) -> list[InputSpec]:
        return [NumberEntry(name='roll', label='2D roll (2–12)', min=2, max=12)]


class PendingLifeEventChoice(PendingInputBase):
    kind: Literal['life_event_choice'] = 'life_event_choice'
    roll: int
    options: list[ConnectionKind] = Field(default_factory=list)

    def event_from_form(self, form: Mapping[str, str]) -> Event:
        raw_kind = literal(
            form_str(form, 'connection_kind', ConnectionKind.RIVAL),
            tuple(ConnectionKind),
            ConnectionKind.RIVAL,
        )
        return Event(
            fulfills=self.pending_id,
            handler=ConnectionKindChoiceHandler(connection_kind=ConnectionKind(raw_kind)),
        )

    def input_specs(self, projection: CharacterProjection) -> list[InputSpec]:
        return [
            Select(
                name='connection_kind',
                label='Connection type',
                options=[('Rival', ConnectionKind.RIVAL.value), ('Enemy', ConnectionKind.ENEMY.value)],
            )
        ]


class PendingLifeEventUnusual(PendingInputBase):
    kind: Literal['life_event_unusual'] = 'life_event_unusual'
    instruction: str = 'Roll 1D on Unusual Events table'

    def event_from_form(self, form: Mapping[str, str]) -> Event:
        return Event(fulfills=self.pending_id, handler=LifeEventUnusualHandler(roll=form_int(form, 'roll', 1)))

    def input_specs(self, projection: CharacterProjection) -> list[InputSpec]:
        return [NumberEntry(name='roll', label='1D roll (1–6)', min=1, max=6)]


class PendingLifeEventBetrayalConvert(PendingInputBase):
    kind: Literal['life_event_betrayal_convert'] = 'life_event_betrayal_convert'

    def event_from_form(self, form: Mapping[str, str]) -> Event:
        raw = form_str(form, 'betrayal_choice', f'0|{ConnectionKind.RIVAL.value}')
        index, kind = raw.split('|', 1)
        return Event(
            fulfills=self.pending_id,
            handler=BetrayalConvertHandler(connection_index=int(index), new_kind=ConnectionKind(kind)),
        )

    def input_specs(self, projection: CharacterProjection) -> list[InputSpec]:
        from ceres.character.domain.connection import Ally, Contact

        options: list[tuple[str, str]] = []
        for index, connection in enumerate(projection.summary.connections):
            if isinstance(connection, (Contact, Ally)):
                label = f'{connection.kind.value.replace("connection_", "").title()} ({connection.origin})'
                options.append((f'{label} → Rival', f'{index}|{ConnectionKind.RIVAL.value}'))
                options.append((f'{label} → Enemy', f'{index}|{ConnectionKind.ENEMY.value}'))
        if not options:
            options = [('Gain Rival', f'0|{ConnectionKind.RIVAL.value}')]
        return [Select(name='betrayal_choice', label='Convert connection', options=options)]


class PendingLifeEventAlienScience(PendingInputBase):
    kind: Literal['life_event_alien_science'] = 'life_event_alien_science'

    def event_from_form(self, form: Mapping[str, str]) -> Event:
        from ceres.character.domain.career.career_events import SkillChoiceHandler, _skill_adapter

        skill = _skill_adapter.validate_json(form_str(form, 'skill', '{}'))
        return Event(fulfills=self.pending_id, handler=SkillChoiceHandler(skill=skill))

    def input_specs(self, projection: CharacterProjection) -> list[InputSpec]:
        from ceres.character.domain.skill_events import build_skill_select_options
        from ceres.character.domain.skills import LifeScience, PhysicalScience, SocialScience

        skills: list[AnySkill] = [LifeScience(), PhysicalScience(), SocialScience(), SpaceScience()]
        return [
            Select(
                name='skill',
                label='Choose a science skill (alien encounter)',
                options=build_skill_select_options(projection, skills, None),
            )
        ]

    def on_skill_chosen(self, projection: CharacterProjection, event: Event) -> None:
        projection.grant_skill(event.skill)
