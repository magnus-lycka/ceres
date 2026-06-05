from ceres.character.input_specs import SelectWorld, WorldFilterCriteria, WorldRef


def test_select_world_keeps_literal_filter_codes():
    spec = SelectWorld(
        name='homeworld',
        label='Choose homeworld',
        sector_abbreviation='Troj',
        reference_world=WorldRef(sector_abbreviation='Troj', hex='2513'),
        filters=WorldFilterCriteria(
            bases=('S', 'W'),
            tech_levels=('8', '9', 'A', 'B', 'C'),
        ),
    )

    assert spec.sector_abbreviation == 'Troj'
    assert spec.reference_world == WorldRef(sector_abbreviation='Troj', hex='2513')
    assert spec.filters.bases == ('S', 'W')
    assert spec.filters.tech_levels == ('8', '9', 'A', 'B', 'C')
