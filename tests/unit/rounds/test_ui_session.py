from pathlib import Path

from nicegui import ui
from nicegui.testing import user_simulation
import pytest

APP_FILE = Path(__file__).parents[3] / 'src/ceres/rounds/ui/app.py'


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
