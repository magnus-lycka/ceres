import pytest
from stuart import render_ship_html, render_ship_pdf, render_ship_typst

from ._output import write_html_output, write_json_output, write_pdf_output, write_typst_output
from .test_alt_dragon import build_alt_dragon
from .test_ambush_hunter_killer_corvette import build_ambush_hunter_killer_corvette
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

pytestmark = pytest.mark.generated_output


@pytest.mark.parametrize(
    ('name', 'builder'),
    [
        ('test_alt_dragon', build_alt_dragon),
        ('test_ambush_hunter_killer_corvette', build_ambush_hunter_killer_corvette),
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


@pytest.mark.parametrize(
    ('name', 'builder'),
    [
        ('test_alt_dragon', build_alt_dragon),
        ('test_ambush_hunter_killer_corvette', build_ambush_hunter_killer_corvette),
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
def test_ship_gallery_pdf_output(name: str, builder) -> None:
    my_ship = builder()
    pdf = render_ship_pdf(my_ship)
    output_path = write_pdf_output(name, pdf)

    assert output_path.exists()
    assert pdf[:4] == b'%PDF'


@pytest.mark.parametrize(
    ('name', 'builder'),
    [
        ('test_alt_dragon', build_alt_dragon),
        ('test_ambush_hunter_killer_corvette', build_ambush_hunter_killer_corvette),
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
def test_ship_gallery_typst_output(name: str, builder) -> None:
    my_ship = builder()
    typst_src = render_ship_typst(my_ship)
    output_path = write_typst_output(name, typst_src)

    assert output_path.exists()
    name = my_ship.ship_class or my_ship.ship_type
    assert name.upper() in typst_src or name in typst_src


@pytest.mark.parametrize(
    ('name', 'builder'),
    [
        ('test_alt_dragon', build_alt_dragon),
        ('test_ambush_hunter_killer_corvette', build_ambush_hunter_killer_corvette),
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
def test_ship_gallery_json_output(name: str, builder) -> None:
    my_ship = builder()
    output_path = write_json_output(name, my_ship)

    assert output_path.exists()
    assert '"tl":' in output_path.read_text(encoding='utf-8')
