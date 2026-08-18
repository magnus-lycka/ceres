"""Run the prototype: `uv run python -m ceres.rounds.ui.app`."""

from nicegui import ui

from ceres.rounds.domain.actor import Actor
from ceres.rounds.domain.situation import Situation
from ceres.rounds.domain.tracks import CharacteristicTrack, HitsTrack
from ceres.rounds.ui.table import RoundsTable


def demo_situation() -> Situation:
    situation = Situation(name='Cargo bay')
    crew = situation.add_party('Crew')
    raiders = situation.add_party('Raiders', initiative=4)
    situation.add_actor(
        Actor(
            name='Rin',
            party=crew,
            track=CharacteristicTrack(strength=8, dexterity=8, endurance=8),
            initiative=7,
        )
    )
    situation.add_actor(
        Actor(
            name='Sana',
            party=crew,
            track=CharacteristicTrack(strength=6, dexterity=9, endurance=7),
            initiative=5,
        )
    )
    thug_track = CharacteristicTrack(strength=7, dexterity=7, endurance=7)
    situation.add_actor(Actor(name='Thug', party=raiders, track=thug_track))
    situation.add_actor(Actor(name='Guard beast', party=raiders, track=HitsTrack(hits=20), initiative=2))
    situation.new_round()
    return situation


@ui.page('/')
def index() -> None:
    RoundsTable(demo_situation()).build()


def main() -> None:
    ui.run(title='Ceres rounds', reload=False, port=8081, show=False)


if __name__ in {'__main__', '__mp_main__'}:
    main()
