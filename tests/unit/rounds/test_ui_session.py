from pathlib import Path

from nicegui import ui
from nicegui.testing import user_simulation
import pytest

APP_FILE = Path(__file__).parents[3] / 'src/ceres/rounds/ui/app.py'
GREY = '#e5e7eb'


@pytest.mark.anyio
async def test_refresh_conditions_and_actor_corrections():
    async with user_simulation(main_file=APP_FILE) as user:
        await user.open('/')
        await user.should_see('Round 1: 0–6s')
        user.find('New round').click()
        await user.should_see('Round 2: 6–12s')

        await user.open('/')

        await user.should_see('Round 2: 6–12s')
        user.find('Attack / damage').click()
        selects = {element.props.get('label'): element for element in user.find(ui.select).elements}
        reaction = next(element for element in user.find(ui.toggle).elements if 'Dive' in element.options)
        selects['Attacker'].value = 'Rin'
        selects['Target'].value = 'Sana'
        reaction.value = 'Dive'

        user.find('Apply').click()

        await user.should_see('Prone')
        user.find('Prone').click()
        await user.should_not_see('Prone')

        user.find('Edit').click()
        await user.should_see('Edit Rin')
        inputs = {element.props.get('label'): element for element in user.find(ui.input).elements}
        numbers = {element.props.get('label'): element for element in user.find(ui.number).elements}
        characteristic_fields = [
            element.props.get('label')
            for element in sorted(user.find(ui.number).elements, key=lambda element: element.id)
            if element.props.get('label', '').startswith(('Max ', 'Current '))
        ]
        assert characteristic_fields == [
            'Max STR',
            'Max DEX',
            'Max END',
            'Current STR',
            'Current DEX',
            'Current END',
        ]
        selects = {element.props.get('label'): element for element in user.find(ui.select).elements}
        assert selects['Initiative source'].value == 'individual'
        assert numbers['Initiative'].value == 7
        inputs['Name'].value = 'Rin corrected'
        numbers['Current END'].value = 3
        numbers['Stun points'].value = 2
        user.find('Save').click()

        await user.should_see('Rin corrected')
        await user.should_see('3/8:-1')
        await user.should_see('2(0)')

        user.find('Edit').click()
        numbers = {element.props.get('label'): element for element in user.find(ui.number).elements}
        selects = {element.props.get('label'): element for element in user.find(ui.select).elements}
        assert selects['Initiative source'].value == 'individual'
        assert numbers['Initiative'].value == 7

        selects['Initiative source'].value = 'party'
        numbers['Initiative'].value = 9
        assert selects['Initiative source'].value == 'individual'
        user.find('Save').click()

        user.find('Edit').click()
        numbers = {element.props.get('label'): element for element in user.find(ui.number).elements}
        assert numbers['Initiative'].value == 9


@pytest.mark.anyio
async def test_the_editor_shows_the_injury_history_and_clears_stun():
    """The first-aid view, and the referee's stand-in for an hour of rest."""
    async with user_simulation(main_file=APP_FILE) as user:
        await user.open('/')
        await user.should_see('Round 1: 0–6s')
        user.find('Attack / damage').click()
        selects = {element.props.get('label'): element for element in user.find(ui.select).elements}
        numbers = {element.props.get('label'): element for element in user.find(ui.number).elements}
        selects['Attacker'].value = 'Rin'
        selects['Target'].value = 'Sana'
        numbers['Lethal points'].value = 4
        numbers['Stun points'].value = 9
        user.find('Apply').click()

        await user.should_see('0/7:-3')
        await user.should_see('3(6)')

        user.find(marker='edit-Sana').click()
        await user.should_see('Injuries')
        await user.should_see('Rounds ago')
        user.find('Clear stun').click()

        await user.should_see('3/7:-1')


@pytest.mark.anyio
async def test_the_injury_view_shows_every_actors_wounds_without_opening_an_editor():
    async with user_simulation(main_file=APP_FILE) as user:
        await user.open('/')
        await user.should_see('Round 1: 0–6s')
        user.find('Attack / damage').click()
        selects = {element.props.get('label'): element for element in user.find(ui.select).elements}
        numbers = {element.props.get('label'): element for element in user.find(ui.number).elements}
        selects['Attacker'].value = 'Rin'
        selects['Target'].value = 'Sana'
        numbers['Lethal points'].value = 4
        user.find('Apply').click()
        await user.should_see('3/7:-1')

        view = next(element for element in user.find(ui.toggle).elements if 'Injuries' in element.options)
        view.value = 'Injuries'

        await user.should_see('Rounds ago')
        await user.should_see('Sana')
        await user.should_see('unhurt')
        user.find('Done').click()

        view = next(element for element in user.find(ui.toggle).elements if 'Injuries' in element.options)
        view.value = 'Round'
        await user.should_see('Ini')


@pytest.mark.anyio
async def test_the_injury_view_greys_an_actor_who_is_done_for_the_round():
    """Acting from the triage view has to give the same feedback as the table."""
    async with user_simulation(main_file=APP_FILE) as user:
        await user.open('/')
        await user.should_see('Round 1: 0–6s')
        view = next(element for element in user.find(ui.toggle).elements if 'Injuries' in element.options)
        view.value = 'Injuries'
        await user.should_see('Rounds ago')
        assert all(GREY not in element._style.values() for element in user.find(marker='injury-Rin').elements)

        user.find('Done').click()

        await user.should_see('Rounds ago')
        assert all(GREY in element._style.values() for element in user.find(marker='injury-Rin').elements)
