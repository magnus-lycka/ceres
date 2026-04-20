import pytest
from stuart import render_ship_html

from ._markdown_output import write_html_output
from .test_alt_dragon import build_alt_dragon
from .test_belt_racer import build_belt_racer
from .test_beowulf import build_beowulf
from .test_boxy_ore_freighter import build_boxy_ore_freighter
from .test_dragon import build_dragon
from .test_florence_medical_scout import build_florence_medical_scout
from .test_gothta_ambush_fighter import build_gothta_ambush_fighter
from .test_poseidon_cargo_boat import build_poseidon_cargo_boat
from .test_revised_beowulf import build_revised_beowulf
from .test_revised_dragon import build_revised_dragon
from .test_strandbell import build_strandbell
from .test_suleiman import build_suleiman
from .test_ultralight_fighter import build_ultralight_fighter


@pytest.mark.parametrize(
    ('name', 'builder'),
    [
        ('test_alt_dragon', build_alt_dragon),
        ('test_belt_racer', build_belt_racer),
        ('test_beowulf', build_beowulf),
        ('test_boxy_ore_freighter', build_boxy_ore_freighter),
        ('test_dragon', build_dragon),
        ('test_florence_medical_scout', build_florence_medical_scout),
        ('test_gothta_ambush_fighter', build_gothta_ambush_fighter),
        ('test_poseidon_100t_tl9', lambda: build_poseidon_cargo_boat(9)),
        ('test_poseidon_100t_tl10', lambda: build_poseidon_cargo_boat(10)),
        ('test_poseidon_100t_tl12', lambda: build_poseidon_cargo_boat(12)),
        ('test_revised_beowulf', build_revised_beowulf),
        ('test_revised_dragon', build_revised_dragon),
        ('test_strandbell', build_strandbell),
        ('test_suleiman', build_suleiman),
        ('test_ultralight_fighter', build_ultralight_fighter),
    ],
)
def test_ship_gallery_html_output(name: str, builder) -> None:
    my_ship = builder()
    html = render_ship_html(my_ship)
    output_path = write_html_output(name, html)

    assert output_path.exists()
    assert '<!doctype html>' in html
    assert '<section class="shell">' in html
    assert '<div class="ship-grid">' in html
    assert my_ship.ship_class in html if my_ship.ship_class else my_ship.ship_type in html
