"""The prototype UI: one table of actors, plus a simple attack dialog.

This is deliberately rough. Its job is to be run at the table so that the real
UI questions get answered by use rather than by argument.
"""

from nicegui import ui

from ceres.character.domain.characteristics import Chars
from ceres.rounds.domain.actions import AttackKind, ReactionKind
from ceres.rounds.domain.actor import Actor, TurnState
from ceres.rounds.domain.situation import Party, Situation
from ceres.rounds.domain.tracks import CharacteristicTrack, DamageTrack, HitsTrack

ROW_COLOURS = {
    TurnState.READY: 'background-color: #dcfce7',  # green: may act
    TurnState.ACTED: 'background-color: #e5e7eb',  # grey: done this round
    TurnState.PENDING: '',
}


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


def stun_cell(track: DamageTrack) -> str:
    """`points(rounds)`, as in 4(11). Blank when unstunned."""
    if isinstance(track, CharacteristicTrack):
        if not track.stun_points and not track.incapacitated_rounds:
            return ''
        return f'{track.stun_points}({track.incapacitated_rounds})'
    if isinstance(track, HitsTrack) and track.stun_total:
        return f'{track.stun_total}{"!" if track.is_incapacitated else ""}'
    return ''


def status_text(actor: Actor) -> str:
    track = actor.track
    if track.is_dead:
        return 'destroyed' if isinstance(track, HitsTrack) and track.is_destroyed else 'dead'
    if track.is_unconscious:
        return 'unconscious'
    if track.is_incapacitated:
        return 'stunned'
    if isinstance(track, HitsTrack) and track.may_be_driven_off:
        return 'may flee'
    return ''


def row_style(actor: Actor) -> str:
    """Out-of-action actors stay grey regardless of their initiative state."""
    if not actor.is_able_to_act:
        return ROW_COLOURS[TurnState.ACTED]
    return ROW_COLOURS[actor.turn_state]


class RoundsTable:
    def __init__(self, situation: Situation):
        self.situation = situation

    def build(self) -> None:
        self.header = ui.row().classes('items-center gap-4')
        self.body = ui.column().classes('w-full')
        self.render()

    def render(self) -> None:
        self.header.clear()
        with self.header:
            ui.label(self.situation.name).classes('text-xl font-bold')
            ui.label().bind_text_from(
                self.situation, 'round_number', lambda n: f'Round {n} — {n * 6}s elapsed'
            ).classes('text-lg')
            ui.button('New round', on_click=self.new_round).props('color=primary')
            ui.button('Add actor', on_click=self.add_actor_dialog).props('outline')
            ui.button('Attack / damage', on_click=self.attack_dialog).props('outline')

        self.body.clear()
        with self.body, ui.grid(columns=10).classes('w-full gap-1 items-center'):
            for heading in ('Name', 'Party', 'Ini', 'STR', 'DEX', 'END', 'Stun', 'React', 'Action', ''):
                ui.label(heading).classes('font-bold text-sm')
            for actor in self.situation.turn_order():
                self.render_row(actor)

    def render_row(self, actor: Actor) -> None:
        style = row_style(actor)
        track = actor.track
        ui.label(actor.name).style(style)
        ui.label(actor.party.name).style(style)
        ui.label(str(actor.initiative_value)).style(style)
        for text in vitality_cells(track):
            ui.label(text).style(style)
        ui.label(stun_cell(track)).style(style)
        ui.label(str(actor.reaction_dm) if actor.reaction_dm else '').style(style)
        ui.label(actor.last_action or status_text(actor)).style(style)
        with ui.row().classes('gap-1').style(style):
            ui.button('Done', on_click=lambda a=actor: self.finish_turn(a)).props('dense size=sm').set_enabled(
                actor.can_act
            )
            ui.button('Wait', on_click=lambda a=actor: self.wait(a)).props('dense size=sm flat').set_enabled(
                actor.can_act
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

    def add_actor_dialog(self) -> None:
        with ui.dialog() as dialog, ui.card():
            ui.label('Add actor').classes('text-lg font-bold')
            name = ui.input('Name')
            party = ui.select([p.name for p in self.situation.parties] + ['<new party>'], label='Party')
            new_party = ui.input('New party name')
            kind = ui.toggle(['Character', 'Animal'], value='Character')
            initiative = ui.number('Ini', value=0, format='%d')
            strength = ui.number('STR', value=7, format='%d')
            dexterity = ui.number('DEX', value=7, format='%d')
            endurance = ui.number('END', value=7, format='%d')
            hits = ui.number('Hits', value=20, format='%d')

            def create() -> None:
                chosen = self.resolve_party(party.value, new_party.value)
                track = (
                    CharacteristicTrack(
                        strength=int(strength.value), dexterity=int(dexterity.value), endurance=int(endurance.value)
                    )
                    if kind.value == 'Character'
                    else HitsTrack(hits=int(hits.value))
                )
                self.situation.add_actor(
                    Actor(name=name.value, party=chosen, track=track, initiative=int(initiative.value))
                )
                dialog.close()
                self.render()

            ui.button('Add', on_click=create)
        dialog.open()

    def resolve_party(self, chosen: str | None, new_name: str) -> Party:
        if chosen and chosen != '<new party>':
            return next(p for p in self.situation.parties if p.name == chosen)
        return self.situation.add_party(new_name or 'Party')

    def attack_dialog(self) -> None:
        """An actor attacks a target, or Other causes environmental injury."""
        names = [a.name for a in self.situation.actors]
        attackers = [a.name for a in self.situation.actors if a.can_act]
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
