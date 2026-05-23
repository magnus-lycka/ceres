from .test_gallery import _SHIPS


def _production_cost(spec) -> float:
    for row in spec.expenses:
        if row.label == 'Production Cost':
            return row.amount
    raise AssertionError('No Production Cost expense row')


def test_ship_specs_tons_and_prices_balance() -> None:
    deviations: list[str] = []
    for name, builder in _SHIPS:
        my_ship = builder()
        spec = my_ship.build_spec()

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
                f'{name}: spec price sum {spec_price:,.2f} vs Production Cost {production_cost:,.2f} '
                f'(delta {price_delta:+,.2f})'
            )

    assert not deviations, '\n'.join(deviations)
