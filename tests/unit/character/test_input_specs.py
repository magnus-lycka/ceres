from ceres.character.input_specs import SelectWorld, WorldFilterCriteria, WorldRef, form_int, form_str, literal


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


def test_form_str_returns_value_when_key_exists():
    assert form_str({'x': 'hello'}, 'x') == 'hello'


def test_form_str_returns_default_when_key_missing():
    assert form_str({}, 'x', 'fallback') == 'fallback'


def test_form_str_returns_default_when_value_is_not_str():
    assert form_str({'x': 42}, 'x', 'fallback') == 'fallback'  # type: ignore[arg-type]  # ty: ignore[invalid-argument-type]


def test_form_int_parses_string_value():
    assert form_int({'n': '7'}, 'n', 0) == 7


def test_form_int_uses_default_when_key_missing():
    assert form_int({}, 'n', 5) == 5


def test_literal_returns_value_when_allowed():
    assert literal('yes', ('yes', 'no'), 'no') == 'yes'


def test_literal_returns_default_when_not_allowed():
    assert literal('maybe', ('yes', 'no'), 'no') == 'no'
