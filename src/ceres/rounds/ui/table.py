"""The prototype UI: one table of actors, plus a simple attack dialog.

This is deliberately rough. Its job is to be run at the table so that the real
UI questions get answered by use rather than by argument.
"""

from dataclasses import dataclass
from functools import partial
from typing import Any

from nicegui import ui

from ceres.character.domain.characteristics import Chars
from ceres.rounds.domain.actions import AttackKind, ReactionKind
from ceres.rounds.domain.actor import Actor, ActorCondition, TurnState
from ceres.rounds.domain.damage import CharacteristicInjury, Injury
from ceres.rounds.domain.situation import ROUND_SECONDS, Situation
from ceres.rounds.domain.tracks import PHYSICAL_CHARACTERISTICS, CharacteristicTrack, DamageTrack, HitsTrack

ROW_COLOURS = {
    TurnState.READY: 'background-color: #dcfce7',  # green: may act
    TurnState.ACTED: 'background-color: #e5e7eb',  # grey: done this round
    TurnState.PENDING: '',
}
ROW_CELL_CLASSES = 'self-stretch flex items-center'


@dataclass
class _ActorEditInputs:
    name: Any
    party: Any
    initiative_source: Any
    initiative: Any
    turn_state: Any
    reaction_dm: Any
    last_action: Any
    waited: Any
    forfeit: Any
    conditions: dict[ActorCondition, Any]


@dataclass
class _CharacteristicEditInputs:
    maximum: dict[Chars, Any]
    current: dict[Chars, Any]
    excess_to: Any
    stun_points: Any
    stun_rounds: Any


@dataclass
class _HitsEditInputs:
    maximum: Any
    current: Any
    stun_points: Any
    stun_rounds: Any


type _DamageEditInputs = _CharacteristicEditInputs | _HitsEditInputs


def round_time_text(round_number: int) -> str:
    """Show the six-second interval occupied by the current round."""
    start = max(round_number - 1, 0) * ROUND_SECONDS
    end = max(round_number, 0) * ROUND_SECONDS
    return f'Round {round_number}: {start}–{end}s'


def characteristic_cell(track: CharacteristicTrack, characteristic: Chars) -> str:
    """`current/max:DM`, as in 5/8:-1, 0/6:-3, 9/9:+1."""
    dm = track.dm(characteristic)
    sign = '+' if dm > 0 else ''
    return f'{track.current(characteristic)}/{track.maximum(characteristic)}:{sign}{dm}'


def vitality_cells(track: DamageTrack) -> tuple[str, str, str]:
    """The STR/DEX/END columns. An animal has only Hits, shown in the END column."""
    if isinstance(track, CharacteristicTrack):
        return tuple(characteristic_cell(track, c) for c in (Chars.STR, Chars.DEX, Chars.END))  # ty: ignore[invalid-return-type]
    if isinstance(track, HitsTrack):
        return '—', '—', f'{track.current}/{track.maximum}'
    return '—', '—', '—'


def incapacitated_rounds(actor: Actor, current_round: int) -> int:
    """Rounds of stun the actor still has to sit out."""
    if actor.incapacitated_until is None:
        return 0
    return max(actor.incapacitated_until - current_round, 0)


def stun_cell(actor: Actor, current_round: int) -> str:
    """`points(rounds)`, with identical meaning for every damage track."""
    rounds = incapacitated_rounds(actor, current_round)
    if not actor.track.stun_points and not rounds:
        return ''
    return f'{actor.track.stun_points}({rounds})'


NOT_TOUCHED = '—'


def injury_headings(track: DamageTrack) -> tuple[str, ...]:
    """The columns of the first-aid view, which differ by what can be hurt."""
    if isinstance(track, CharacteristicTrack):
        return ('Rounds ago', 'Kind', *(c.value for c in PHYSICAL_CHARACTERISTICS))
    return 'Rounds ago', 'Kind', 'Hits'


def injury_rows(actor: Actor, current_round: int) -> tuple[tuple[str, ...], ...]:
    """One line per hit, oldest first: how long ago it landed and what it cost.

    First aid must be applied within a minute — ten rounds — so the age of a
    wound decides whether it can still be treated. Wounds carried out of an
    earlier fight are past that window and read `earlier`.
    """
    return tuple(_injury_row(injury, current_round) for injury in actor.track.injuries)


def injury_list_headings() -> tuple[str, ...]:
    return ('Name', 'Party', 'Rounds ago', 'Kind', *(c.value for c in PHYSICAL_CHARACTERISTICS))


def injury_list_rows(situation: Situation) -> tuple[tuple[str, ...], ...]:
    """Every actor's injuries at once, for deciding whom to treat first."""
    return tuple(row for _, row, _leads in injury_list_entries(situation))


def injury_list_entries(situation: Situation) -> tuple[tuple[Actor, tuple[str, ...], bool], ...]:
    """One line per hit under the actor who took it, in the table's own order.

    Each entry carries its actor so the view can offer Done and Edit, and says
    whether it leads that actor's lines — only the first one is labelled. An
    animal's Hits sit in the END column, as they do in the round table.
    """
    entries: list[tuple[Actor, tuple[str, ...], bool]] = []
    for actor in situation.turn_order():
        injuries = actor.track.injuries
        if not injuries:
            entries.append((actor, (actor.name, actor.party.name, NOT_TOUCHED, 'unhurt', *(NOT_TOUCHED,) * 3), True))
            continue
        for position, injury in enumerate(injuries):
            label = (actor.name, actor.party.name) if position == 0 else ('', '')
            entries.append((actor, (*label, *_injury_line(injury, situation.round_number)), position == 0))
    return tuple(entries)


def _injury_row(injury: Injury, current_round: int) -> tuple[str, ...]:
    """The per-actor view, where an animal has one Hits column rather than three."""
    age, kind, *reductions = _injury_line(injury, current_round)
    return (age, kind, *reductions) if isinstance(injury, CharacteristicInjury) else (age, kind, reductions[-1])


def _injury_line(injury: Injury, current_round: int) -> tuple[str, ...]:
    """Age, kind, and what it took off STR, DEX and END — Hits count as END."""
    age = 'earlier' if injury.is_earlier else str(injury.rounds_ago(current_round))
    if isinstance(injury, CharacteristicInjury):
        return (age, injury.kind.value, *(_reduction(injury.reduction_to(c)) for c in PHYSICAL_CHARACTERISTICS))
    return age, injury.kind.value, NOT_TOUCHED, NOT_TOUCHED, _reduction(injury.total)


def _reduction(points: int) -> str:
    return f'-{points}' if points else NOT_TOUCHED


def status_text(actor: Actor, current_round: int) -> str:
    track = actor.track
    if track.is_dead:
        return 'destroyed' if isinstance(track, HitsTrack) and track.is_destroyed else 'dead'
    statuses: list[str] = []
    if track.is_unconscious:
        statuses.append('unconscious')
    if actor.is_incapacitated(current_round):
        statuses.append('stunned')
    if isinstance(track, HitsTrack) and track.may_be_driven_off:
        statuses.append('may flee')
    return ', '.join(statuses)


def condition_tags(actor: Actor) -> tuple[str, ...]:
    """Stable labels for persistent, referee-managed actor conditions."""
    return tuple(condition.value for condition in sorted(actor.conditions, key=lambda condition: condition.value))


def row_style(actor: Actor, current_round: int) -> str:
    """Out-of-action actors stay grey regardless of their initiative state."""
    if not actor.is_able_to_act(current_round):
        return ROW_COLOURS[TurnState.ACTED]
    return ROW_COLOURS[actor.turn_state]


ROUND_VIEW = 'Round'
INJURY_VIEW = 'Injuries'


class RoundsTable:
    def __init__(self, situation: Situation):
        self.situation = situation
        self.view = ROUND_VIEW

    def build(self) -> None:
        self.header = ui.row().classes('items-center gap-4')
        self.body = ui.column().classes('w-full')
        self.render()

    def render(self) -> None:
        self.header.clear()
        with self.header:
            ui.label(self.situation.name).classes('text-xl font-bold')
            ui.label().bind_text_from(self.situation, 'round_number', round_time_text).classes('text-lg')
            ui.button('New round', on_click=self.new_round).props('color=primary')
            ui.button('Attack / damage', on_click=self.attack_dialog).props('outline')
            ui.toggle([ROUND_VIEW, INJURY_VIEW], value=self.view, on_change=self.show_view).props('dense')

        self.body.clear()
        with self.body:
            self.render_injury_list() if self.view == INJURY_VIEW else self.render_round_table()

    def show_view(self, event: Any) -> None:
        self.view = event.value
        self.render()

    def render_round_table(self) -> None:
        with ui.grid(columns=11).classes('w-full gap-1 items-center'):
            for heading in ('Name', 'Party', 'Ini', 'STR', 'DEX', 'END', 'Stun', 'React', 'Action', 'Status', ''):
                ui.label(heading).classes('font-bold text-sm')
            for actor in self.situation.turn_order():
                self.render_row(actor)

    def render_injury_list(self) -> None:
        """Read-only triage: every wound, whose it is, and how old it is.

        Rows carry the same colours as the round table, so acting from here
        gives the same feedback: green may act, grey is done or out of it.
        """
        headings = injury_list_headings()
        with ui.grid(columns=len(headings) + 1).classes('w-full gap-1 items-center'):
            for heading in (*headings, ''):
                ui.label(heading).classes('font-bold text-sm')
            for actor, row, leads in injury_list_entries(self.situation):
                style = row_style(actor, self.situation.round_number)
                for value in row:
                    ui.label(value).classes(ROW_CELL_CLASSES).style(style).mark(f'injury-{actor.name}')
                self.render_injury_list_buttons(actor, leads, style)

    def render_injury_list_buttons(self, actor: Actor, leads: bool, style: str) -> None:
        with ui.row().classes('gap-1 self-stretch items-center').style(style):
            if not leads:
                return
            ui.button('Done', on_click=lambda a=actor: self.finish_turn(a)).props('dense size=sm').set_enabled(
                actor.can_act(self.situation.round_number)
            )
            ui.button('Edit', on_click=lambda a=actor: self.edit_actor_dialog(a)).props('dense size=sm flat')

    def render_row(self, actor: Actor) -> None:
        current_round = self.situation.round_number
        style = row_style(actor, current_round)
        track = actor.track
        ui.label(actor.name).classes(ROW_CELL_CLASSES).style(style)
        ui.label(actor.party.name).classes(ROW_CELL_CLASSES).style(style)
        ui.label(str(actor.initiative_value)).classes(ROW_CELL_CLASSES).style(style)
        for text in vitality_cells(track):
            ui.label(text).classes(ROW_CELL_CLASSES).style(style)
        ui.label(stun_cell(actor, current_round)).classes(ROW_CELL_CLASSES).style(style)
        ui.label(str(actor.reaction_dm) if actor.reaction_dm else '').classes(ROW_CELL_CLASSES).style(style)
        ui.label(actor.last_action).classes(ROW_CELL_CLASSES).style(style)
        with ui.row().classes('self-stretch items-center gap-1').style(style):
            ui.label(status_text(actor, current_round))
            for condition in sorted(actor.conditions, key=lambda item: item.value):
                ui.chip(
                    condition.value,
                    removable=True,
                    on_click=partial(self.clear_condition, actor, condition),
                    on_value_change=lambda event, a=actor, c=condition: (
                        self.clear_condition(a, c) if not event.value else None
                    ),
                ).props('dense')
        with ui.row().classes('gap-1').style(style):
            can_act = actor.can_act(current_round)
            ui.button('Done', on_click=lambda a=actor: self.finish_turn(a)).props('dense size=sm').set_enabled(can_act)
            ui.button('Wait', on_click=lambda a=actor: self.wait(a)).props('dense size=sm flat').set_enabled(can_act)
            ui.button('Edit', on_click=lambda a=actor: self.edit_actor_dialog(a)).props('dense size=sm flat').mark(
                f'edit-{actor.name}'
            )

    def new_round(self) -> None:
        self.situation.new_round()
        for actor in self.situation.actors:
            actor.last_action = ''
        self.render()

    def finish_turn(self, actor: Actor) -> None:
        self.situation.finish_turn(actor)
        self.render()

    def wait(self, actor: Actor) -> None:
        self.situation.wait(actor)
        self.render()

    def clear_condition(self, actor: Actor, condition: ActorCondition) -> None:
        self.situation.clear_condition(actor, condition)
        self.render()

    def edit_actor_dialog(self, actor: Actor) -> None:
        """Edit stored combat facts; statuses remain derived from those facts."""
        with ui.dialog() as dialog, ui.card().classes('w-[42rem] max-w-full'):
            ui.label(f'Edit {actor.name}').classes('text-lg font-bold')
            actor_inputs = self._build_actor_edit_inputs(actor)
            ui.separator()
            damage_inputs = self._build_damage_edit_inputs(actor)
            self._show_injury_history(actor)
            with ui.row().classes('justify-end w-full'):
                ui.button('Clear stun', on_click=lambda: self._clear_stun(actor, dialog)).props('flat')
                ui.space()
                ui.button('Cancel', on_click=dialog.close).props('flat')
                ui.button(
                    'Save',
                    on_click=lambda: self._save_actor_edit(actor, actor_inputs, damage_inputs, dialog),
                )
        dialog.open()

    def _show_injury_history(self, actor: Actor) -> None:
        """What each hit did and how long ago, for judging the first-aid window."""
        rows = injury_rows(actor, self.situation.round_number)
        if not rows:
            return
        headings = injury_headings(actor.track)
        ui.label('Injuries').classes('font-bold')
        with ui.grid(columns=len(headings)).classes('w-full gap-1'):
            for heading in headings:
                ui.label(heading).classes('text-sm font-bold')
            for row in rows:
                for value in row:
                    ui.label(value).classes('text-sm')

    def _clear_stun(self, actor: Actor, dialog: Any) -> None:
        """An hour of rest, applied by the referee rather than inferred (:366)."""
        actor.clear_stun()
        dialog.close()
        self.render()

    def _build_actor_edit_inputs(self, actor: Actor) -> _ActorEditInputs:
        with ui.grid(columns=2).classes('w-full gap-3'):
            name = ui.input('Name', value=actor.name)
            party_options = {str(index): party.name for index, party in enumerate(self.situation.parties)}
            party_index = str(self.situation.parties.index(actor.party))
            party = ui.select(party_options, value=party_index, label='Party')
            initiative_source = ui.select(
                {'individual': 'Individual', 'party': 'Party'},
                value='individual' if actor.initiative is not None else 'party',
                label='Initiative source',
            )
            initiative = ui.number(
                'Initiative',
                value=actor.initiative_value,
                format='%d',
                on_change=lambda: initiative_source.set_value('individual'),
            )
            turn_state = ui.select(
                {state.value: state.value.title() for state in TurnState},
                value=actor.turn_state.value,
                label='Turn state',
            )
            reaction_dm = ui.number('Reaction DM', value=actor.reaction_dm, format='%d')
            last_action = ui.input('Last action', value=actor.last_action)
            waited = ui.checkbox('Waiting', value=actor.waited)
            forfeit = ui.checkbox('Forfeit next turn', value=actor.forfeits_next_turn)
            conditions = {
                condition: ui.checkbox(condition.value, value=condition in actor.conditions)
                for condition in ActorCondition
            }
        return _ActorEditInputs(
            name,
            party,
            initiative_source,
            initiative,
            turn_state,
            reaction_dm,
            last_action,
            waited,
            forfeit,
            conditions,
        )

    def _build_damage_edit_inputs(self, actor: Actor) -> _DamageEditInputs:
        track = actor.track
        if isinstance(track, CharacteristicTrack):
            ui.label('Characteristics').classes('font-bold')
            maximum: dict[Chars, Any] = {}
            current: dict[Chars, Any] = {}
            with ui.grid(columns=3).classes('w-full gap-3'):
                for characteristic in PHYSICAL_CHARACTERISTICS:
                    maximum[characteristic] = ui.number(
                        f'Max {characteristic.value}', value=track.maximum(characteristic), format='%d'
                    )
                for characteristic in PHYSICAL_CHARACTERISTICS:
                    current[characteristic] = ui.number(
                        f'Current {characteristic.value}', value=track.current(characteristic), format='%d'
                    )
                excess_to = ui.select(
                    {Chars.DEX.value: 'DEX first', Chars.STR.value: 'STR first'},
                    value=track.excess_to.value,
                    label='Excess damage',
                )
            common = self._build_stun_edit_inputs(actor)
            return _CharacteristicEditInputs(maximum, current, excess_to, *common)

        if not isinstance(track, HitsTrack):
            msg = f'no editor for {type(track).__name__}'
            raise TypeError(msg)
        ui.label('Hits').classes('font-bold')
        with ui.grid(columns=2).classes('w-full gap-3'):
            maximum_hits = ui.number('Max Hits', value=track.maximum, format='%d')
            current_hits = ui.number('Current Hits', value=track.current, format='%d')
        common = self._build_stun_edit_inputs(actor)
        return _HitsEditInputs(maximum_hits, current_hits, *common)

    def _build_stun_edit_inputs(self, actor: Actor) -> tuple[Any, Any]:
        remaining = incapacitated_rounds(actor, self.situation.round_number)
        with ui.grid(columns=2).classes('w-full gap-3'):
            stun_points = ui.number('Stun points', value=actor.track.stun_points, format='%d')
            stun_rounds = ui.number('Stun rounds', value=remaining, format='%d')
        return stun_points, stun_rounds

    def _save_actor_edit(
        self,
        actor: Actor,
        actor_inputs: _ActorEditInputs,
        damage_inputs: _DamageEditInputs,
        dialog: Any,
    ) -> None:
        try:
            self._apply_actor_edit(actor, actor_inputs, damage_inputs)
        except ValueError as error:
            ui.notify(str(error), type='negative')
            return
        dialog.close()
        self.render()

    def _apply_actor_edit(
        self,
        actor: Actor,
        actor_inputs: _ActorEditInputs,
        damage_inputs: _DamageEditInputs,
    ) -> None:
        name = actor_inputs.name.value.strip()
        if not name:
            msg = 'name cannot be empty'
            raise ValueError(msg)
        self._correct_damage_track(actor.track, damage_inputs)
        self.situation.correct_actor(
            actor,
            name=name,
            party=self.situation.parties[int(actor_inputs.party.value)],
            initiative=self._integer(actor_inputs.initiative)
            if actor_inputs.initiative_source.value == 'individual'
            else None,
            turn_state=TurnState(actor_inputs.turn_state.value),
            reaction_dm=self._integer(actor_inputs.reaction_dm),
            last_action=actor_inputs.last_action.value,
            conditions={condition for condition, field in actor_inputs.conditions.items() if field.value},
            forfeit_next_turn=actor_inputs.forfeit.value,
            waited=actor_inputs.waited.value,
            incapacitated_rounds=self._integer(damage_inputs.stun_rounds),
        )

    @staticmethod
    def _correct_damage_track(track: DamageTrack, inputs: _DamageEditInputs) -> None:
        if isinstance(track, CharacteristicTrack) and isinstance(inputs, _CharacteristicEditInputs):
            track.correct_state(
                maximum={c: RoundsTable._integer(inputs.maximum[c]) for c in PHYSICAL_CHARACTERISTICS},
                current={c: RoundsTable._integer(inputs.current[c]) for c in PHYSICAL_CHARACTERISTICS},
                stun_points=RoundsTable._integer(inputs.stun_points),
            )
            track.excess_to = Chars(inputs.excess_to.value)
            return
        if isinstance(track, HitsTrack) and isinstance(inputs, _HitsEditInputs):
            track.correct_state(
                maximum=RoundsTable._integer(inputs.maximum),
                current=RoundsTable._integer(inputs.current),
                stun_points=RoundsTable._integer(inputs.stun_points),
            )
            return
        msg = 'damage editor does not match actor type'
        raise ValueError(msg)

    @staticmethod
    def _integer(field: Any) -> int:
        if field.value is None:
            msg = 'numeric fields cannot be empty'
            raise ValueError(msg)
        return int(field.value)

    def attack_dialog(self) -> None:
        """An actor attacks a target, or Other causes environmental injury."""
        names = [a.name for a in self.situation.actors]
        attackers = [a.name for a in self.situation.actors if a.can_act(self.situation.round_number)]
        with ui.dialog() as dialog, ui.card():
            ui.label('Attack / damage').classes('text-lg font-bold')
            attacker = ui.select(['Other', *attackers], value='Other', label='Attacker')
            target = ui.select(names, label='Target')
            attack_kind = ui.toggle(
                [AttackKind.MELEE.value, AttackKind.RANGED.value],
                value=AttackKind.RANGED.value,
            ).props('label="Attack kind (actor source only)"')
            reaction = ui.toggle(['None', *ReactionKind], value='None')
            lethal = ui.number('Lethal points', value=0, format='%d')
            stun = ui.number('Stun points', value=0, format='%d')
            excess_to = ui.toggle(['DEX', 'STR'], value='DEX')

            def resolve() -> None:
                victim = next(a for a in self.situation.actors if a.name == target.value)
                if reaction.value != 'None':
                    self.situation.react(victim, ReactionKind(reaction.value))
                if isinstance(victim.track, CharacteristicTrack):
                    victim.track.excess_to = Chars.DEX if excess_to.value == 'DEX' else Chars.STR
                if attacker.value != 'Other':
                    assailant = next(a for a in self.situation.actors if a.name == attacker.value)
                    self.situation.attack(
                        assailant,
                        victim,
                        AttackKind(attack_kind.value),
                        lethal=int(lethal.value),
                        stun=int(stun.value),
                    )
                else:
                    self.situation.attack(None, victim, lethal=int(lethal.value), stun=int(stun.value))
                dialog.close()
                self.render()

            ui.button('Apply', on_click=resolve)
        dialog.open()
