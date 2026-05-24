import pytest

from ceres.make.ship.ship import Ship
from ceres.make.ship.spec import ShipSpec, SpecRow
from ceres.make.ship.view import collapsed_main_rows

from .test_gallery import _SHIPS

type ShipSpecAnalysis = tuple[str, Ship, ShipSpec, list[SpecRow]]

_POWER_LOADS_BY_SECTION = {
    'Jump': 'jump_power_load',
    'Propulsion': 'maneuver_power_load',
    'Fuel': 'fuel_power_load',
    'Sensors': 'sensor_power_load',
    'Weapons': 'weapon_power_load',
}


@pytest.fixture(scope='module')
def ship_spec_analyses() -> list[ShipSpecAnalysis]:
    analyses: list[ShipSpecAnalysis] = []
    for name, builder in _SHIPS:
        my_ship = builder()
        spec = my_ship.build_spec()
        analyses.append((name, my_ship, spec, collapsed_main_rows(spec)))
    return analyses


def _production_cost(spec) -> float:
    for row in spec.expenses:
        if row.label == 'Production Cost':
            return row.amount
    raise AssertionError('No Production Cost expense row')


def test_ship_specs_tons_and_prices_balance(ship_spec_analyses: list[ShipSpecAnalysis]) -> None:
    deviations: list[str] = []
    for name, _my_ship, spec, _collapsed_rows in ship_spec_analyses:
        hull_rows = [row for row in spec.rows if row.emphasize_tons]
        if len(hull_rows) != 1:
            deviations.append(f'{name}: expected one emphasized hull tons row, found {len(hull_rows)}')
            continue

        hull_tons = hull_rows[0].tons
        if hull_tons is None:
            deviations.append(f'{name}: emphasized hull row has no tons value')
            continue

        other_tons = sum(row.tons for row in spec.rows if row.tons is not None and not row.emphasize_tons)
        tons_delta = other_tons - hull_tons
        if abs(tons_delta) > 0.005:
            deviations.append(
                f'{name}: spec tons sum {other_tons:.2f} vs hull {hull_tons:.2f} (delta {tons_delta:+.2f})'
            )

        spec_price = sum(row.cost for row in spec.rows if row.cost is not None)
        production_cost = _production_cost(spec)
        price_delta = spec_price - production_cost
        if abs(price_delta) > 0.005:
            deviations.append(
                f'{name}: spec price sum {spec_price:,.2f} vs Production Cost '
                f'{production_cost:,.2f} '
                f'(delta {price_delta:+,.2f})'
            )

    assert not deviations, '\n'.join(deviations)


def test_ship_specs_power_rows_match_model_power_loads(
    ship_spec_analyses: list[ShipSpecAnalysis],
) -> None:
    deviations: list[str] = []
    for name, my_ship, spec, _collapsed_rows in ship_spec_analyses:
        produced_power = sum(row.power for row in spec.rows if row.power is not None and row.emphasize_power)
        production_delta = produced_power - my_ship.available_power
        if abs(production_delta) > 0.005:
            deviations.append(
                f'{name}: spec produced power {produced_power:.2f} vs available power '
                f'{my_ship.available_power:.2f} (delta {production_delta:+.2f})'
            )

        basic_rows = [row for row in spec.rows if row.item == 'Basic Ship Systems' and row.power is not None]
        if len(basic_rows) != 1:
            deviations.append(f'{name}: expected one Basic Ship Systems power row, found {len(basic_rows)}')
            continue
        basic_power = basic_rows[0].power
        if basic_power is None:
            deviations.append(f'{name}: Basic Ship Systems row has no power value')
            continue
        basic_delta = basic_power - my_ship.basic_hull_power_load
        if abs(basic_delta) > 0.005:
            deviations.append(
                f'{name}: spec basic power {basic_power:.2f} vs model basic power '
                f'{my_ship.basic_hull_power_load:.2f} (delta {basic_delta:+.2f})'
            )

        for section, attribute_name in _POWER_LOADS_BY_SECTION.items():
            spec_load = -sum(
                row.power
                for row in spec.rows_for_section(section)
                if row.power is not None and row.power < 0 and not row.emphasize_power
            )
            model_load = getattr(my_ship, attribute_name)
            load_delta = spec_load - model_load
            if abs(load_delta) > 0.005:
                deviations.append(
                    f'{name}: spec {section} power load {spec_load:.2f} vs model {attribute_name} '
                    f'{model_load:.2f} (delta {load_delta:+.2f})'
                )

        non_drive_load = -sum(
            row.power
            for row in spec.rows
            if row.section.value not in {'Jump', 'Propulsion'}
            and row.item != 'Basic Ship Systems'
            and row.power is not None
            and row.power < 0
            and not row.emphasize_power
        )
        spec_total_load = basic_power + max(my_ship.jump_power_load, my_ship.maneuver_power_load) + non_drive_load
        total_delta = spec_total_load - my_ship.total_power_load
        if abs(total_delta) > 0.005:
            deviations.append(
                f'{name}: spec total power load {spec_total_load:.2f} vs model total power load '
                f'{my_ship.total_power_load:.2f} (delta {total_delta:+.2f})'
            )

    assert not deviations, '\n'.join(deviations)


def test_ship_specs_do_not_render_non_positive_cargo_hold_rows(
    ship_spec_analyses: list[ShipSpecAnalysis],
) -> None:
    deviations: list[str] = []
    for name, _my_ship, _spec, collapsed_rows in ship_spec_analyses:
        for row in collapsed_rows:
            is_non_positive_cargo_hold = (
                row.section.value == 'Cargo' and row.item == 'Cargo Hold' and row.tons is not None
            )
            if is_non_positive_cargo_hold and row.tons < 0.005:
                deviations.append(f'{name}: {row.section.value} row {row.item!r} renders as {row.tons:.2f} tons')

    assert not deviations, '\n'.join(deviations)


def test_ship_specs_do_not_render_multiple_unlabelled_cargo_holds(
    ship_spec_analyses: list[ShipSpecAnalysis],
) -> None:
    deviations: list[str] = []
    for name, _my_ship, _spec, collapsed_rows in ship_spec_analyses:
        unlabelled_cargo_holds = [
            row for row in collapsed_rows if row.section.value == 'Cargo' and row.item == 'Cargo Hold'
        ]
        if len(unlabelled_cargo_holds) > 1:
            tons = ', '.join(f'{row.tons:.2f}' for row in unlabelled_cargo_holds if row.tons is not None)
            deviations.append(f'{name}: renders {len(unlabelled_cargo_holds)} unlabelled Cargo Hold rows ({tons} tons)')

    assert not deviations, '\n'.join(deviations)


def test_ship_specs_do_not_render_duplicate_collapsed_rows(
    ship_spec_analyses: list[ShipSpecAnalysis],
) -> None:
    deviations: list[str] = []
    for name, _my_ship, _spec, collapsed_rows in ship_spec_analyses:
        seen: set[tuple] = set()
        for row in collapsed_rows:
            notes = tuple((note.category, note.message) for note in row.notes)
            key = (row.section.value, row.item, row.tons, row.cost, row.power, notes)
            if key in seen:
                deviations.append(f'{name}: duplicate collapsed row {row.section.value} / {row.item!r}')
            seen.add(key)

    assert not deviations, '\n'.join(deviations)


def test_ship_spec_collapse_preserves_tons_and_cost_by_section(
    ship_spec_analyses: list[ShipSpecAnalysis],
) -> None:
    deviations: list[str] = []
    for name, _my_ship, spec, collapsed_rows in ship_spec_analyses:
        for section in {row.section for row in spec.rows}:
            raw_tons = sum(row.tons for row in spec.rows if row.section == section and row.tons is not None)
            collapsed_tons = sum(row.tons for row in collapsed_rows if row.section == section and row.tons is not None)
            tons_delta = collapsed_tons - raw_tons
            if abs(tons_delta) > 0.005:
                deviations.append(
                    f'{name}: collapsed {section.value} tons {collapsed_tons:.2f} '
                    f'vs raw {raw_tons:.2f} '
                    f'(delta {tons_delta:+.2f})'
                )

            raw_cost = sum(row.cost for row in spec.rows if row.section == section and row.cost is not None)
            collapsed_cost = sum(row.cost for row in collapsed_rows if row.section == section and row.cost is not None)
            cost_delta = collapsed_cost - raw_cost
            if abs(cost_delta) > 0.5:
                deviations.append(
                    f'{name}: collapsed {section.value} cost {collapsed_cost:,.0f} '
                    f'vs raw {raw_cost:,.0f} '
                    f'(delta {cost_delta:+,.0f})'
                )

    assert not deviations, '\n'.join(deviations)


def test_ship_spec_collapse_preserves_power_by_section_and_kind(
    ship_spec_analyses: list[ShipSpecAnalysis],
) -> None:
    deviations: list[str] = []
    for name, _my_ship, spec, collapsed_rows in ship_spec_analyses:
        for section in {row.section for row in spec.rows}:
            for kind, predicate in [
                ('produced', lambda row: row.power is not None and row.emphasize_power),
                (
                    'consumed',
                    lambda row: row.power is not None and row.power < 0 and not row.emphasize_power,
                ),
            ]:
                raw_power = sum(row.power for row in spec.rows if row.section == section and predicate(row))
                collapsed_power = sum(row.power for row in collapsed_rows if row.section == section and predicate(row))
                power_delta = collapsed_power - raw_power
                if abs(power_delta) > 0.005:
                    deviations.append(
                        f'{name}: collapsed {section.value} {kind} power '
                        f'{collapsed_power:.2f} vs raw '
                        f'{raw_power:.2f} (delta {power_delta:+.2f})'
                    )

    assert not deviations, '\n'.join(deviations)
