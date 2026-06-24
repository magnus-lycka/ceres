import inspect

import pytest

from ceres.report import render_pdf_source, render_ship_html, render_ship_typst
from tests.approval.ships.test_90t_non_gravity_rdrive import build_90t_non_gravity_rdrive
from tests.approval.ships.test_acrux_heavy_cruiser import build_acrux_heavy_cruiser
from tests.approval.ships.test_almeida_laboratory_station import build_almeida_laboratory_station
from tests.approval.ships.test_alt_dragon import build_alt_dragon
from tests.approval.ships.test_ambush_hunter_killer_corvette import build_ambush_hunter_killer_corvette
from tests.approval.ships.test_beagle_laboratory_ship import build_beagle_laboratory_ship
from tests.approval.ships.test_belt_racer import build_belt_racer
from tests.approval.ships.test_beowulf import build_beowulf
from tests.approval.ships.test_boxy_ore_freighter import build_boxy_ore_freighter
from tests.approval.ships.test_civilian_hopper import build_civilian_hopper
from tests.approval.ships.test_dolphin_extended_scout_courier import build_dolphin_extended_scout_courier
from tests.approval.ships.test_dragon import build_dragon
from tests.approval.ships.test_florence_medical_scout import build_florence_medical_scout
from tests.approval.ships.test_freight_handler_pod import build_freight_handler_pod
from tests.approval.ships.test_gothta_ambush_fighter import build_gothta_ambush_fighter
from tests.approval.ships.test_king_kay_luxury_liner import build_king_kay
from tests.approval.ships.test_pinnace_with_20_ton_fuel_capacity import build_pinnace_with_20_ton_fuel_capacity
from tests.approval.ships.test_poseidon_cargo_boat import (
    build_poseidon_cargo_boat_tl9,
    build_poseidon_cargo_boat_tl10,
    build_poseidon_cargo_boat_tl12,
)
from tests.approval.ships.test_revised_beowulf import build_revised_beowulf
from tests.approval.ships.test_revised_dragon import build_revised_dragon
from tests.approval.ships.test_safari_ship import build_safari_ship
from tests.approval.ships.test_serrano_laboratory_station import build_serrano_laboratory_station
from tests.approval.ships.test_small_scout_base import build_small_scout_base
from tests.approval.ships.test_strandbell import build_strandbell
from tests.approval.ships.test_suleiman import build_suleiman
from tests.approval.ships.test_ultralight_fighter import build_ultralight_fighter
from tests.approval.ships.test_valiant_light_cruiser import build_valiant_light_cruiser

from ._output import write_html_output, write_json_output, write_pdf_output, write_typst_output

pytestmark = pytest.mark.generated_output

_SHIPS = sorted(
    [
        ('test_90t_non_gravity_rdrive', build_90t_non_gravity_rdrive),
        ('test_acrux_heavy_cruiser', build_acrux_heavy_cruiser),
        ('test_almeida_laboratory_station', build_almeida_laboratory_station),
        ('test_alt_dragon', build_alt_dragon),
        ('test_ambush_hunter_killer_corvette', build_ambush_hunter_killer_corvette),
        ('test_beagle_laboratory_ship', build_beagle_laboratory_ship),
        ('test_belt_racer', build_belt_racer),
        ('test_beowulf', build_beowulf),
        ('test_boxy_ore_freighter', build_boxy_ore_freighter),
        ('test_civilian_hopper', build_civilian_hopper),
        ('test_dolphin_extended_scout_courier', build_dolphin_extended_scout_courier),
        ('test_dragon', build_dragon),
        ('test_florence_medical_scout', build_florence_medical_scout),
        ('test_freight_handler_pod', build_freight_handler_pod),
        ('test_gothta_ambush_fighter', build_gothta_ambush_fighter),
        ('test_king_kay_luxury_liner', build_king_kay),
        ('test_pinnace_with_20_ton_fuel_capacity', build_pinnace_with_20_ton_fuel_capacity),
        ('test_poseidon_100t_tl9', build_poseidon_cargo_boat_tl9),
        ('test_poseidon_100t_tl10', build_poseidon_cargo_boat_tl10),
        ('test_poseidon_100t_tl12', build_poseidon_cargo_boat_tl12),
        ('test_revised_beowulf', build_revised_beowulf),
        ('test_revised_dragon', build_revised_dragon),
        ('test_safari_ship', build_safari_ship),
        ('test_serrano_laboratory_station', build_serrano_laboratory_station),
        ('test_small_scout_base', build_small_scout_base),
        ('test_strandbell', build_strandbell),
        ('test_suleiman', build_suleiman),
        ('test_ultralight_fighter', build_ultralight_fighter),
        ('test_valiant_light_cruiser', build_valiant_light_cruiser),
    ],
    key=lambda entry: (entry[1]().ship_class or entry[1]().ship_type).lower(),
)


def _builder_note(builder) -> str | None:
    doc = inspect.cleandoc(builder.__doc__ or '')
    return doc if doc.startswith('Note:') else None


@pytest.mark.parametrize(('name', 'builder'), _SHIPS)
def test_ship_gallery_html_output(name: str, builder) -> None:
    my_ship = builder()
    html = render_ship_html(my_ship)
    output_path = write_html_output(name, html)

    assert output_path.exists()
    assert '<!doctype html>' in html
    assert '<section class="shell">' in html
    assert '<div class="ship-grid">' in html
    assert my_ship.ship_class in html if my_ship.ship_class else my_ship.ship_type in html


def _render_ship_gallery_typst() -> str:
    return '\n#pagebreak()\n'.join(
        render_ship_typst(builder(), note=_builder_note(builder)) for _name, builder in _SHIPS
    )


def test_ship_gallery_pdf_output() -> None:
    typst_src = _render_ship_gallery_typst()
    typst_output_path = write_typst_output('ships_gallery', typst_src)
    pdf = render_pdf_source(typst_src)
    output_path = write_pdf_output('ships_gallery', pdf)

    assert typst_output_path.exists()
    assert output_path.exists()
    assert pdf[:4] == b'%PDF'


@pytest.mark.parametrize(('name', 'builder'), _SHIPS)
def test_ship_gallery_typst_output(name: str, builder) -> None:
    my_ship = builder()
    typst_src = render_ship_typst(my_ship, note=_builder_note(builder))
    output_path = write_typst_output(name, typst_src)

    assert output_path.exists()
    name = my_ship.ship_class or my_ship.ship_type
    assert name.upper() in typst_src or name in typst_src


@pytest.mark.parametrize(('name', 'builder'), _SHIPS)
def test_ship_gallery_json_output(name: str, builder) -> None:
    my_ship = builder()
    output_path = write_json_output(name, my_ship)

    assert output_path.exists()
    assert '"tl":' in output_path.read_text(encoding='utf-8')
