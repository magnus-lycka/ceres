from ceres.build.ship.text import collapse_repeated_labels, format_counted_label, optional_count


def test_format_counted_label_uses_multiplication_sign_for_plural_counts():
    assert format_counted_label('Staterooms', 10) == 'Staterooms × 10'


def test_format_counted_label_leaves_single_items_plain():
    assert format_counted_label('Pilot', 1) == 'Pilot'
    assert format_counted_label('Pilot', None) == 'Pilot'


def test_optional_count_hides_singular_counts():
    assert optional_count(1) is None
    assert optional_count(3) == 3


def test_collapse_repeated_labels_preserves_order_and_counts():
    assert collapse_repeated_labels(['Pulse Laser', 'Missile Rack', 'Pulse Laser', 'Pulse Laser']) == [
        'Pulse Laser × 3',
        'Missile Rack',
    ]
