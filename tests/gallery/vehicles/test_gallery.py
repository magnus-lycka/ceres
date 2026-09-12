"""Render every source-derived vehicle design, as the robot and ship galleries do."""

import pytest

from ceres.make.vehicle.report import render_vehicle_pdf, render_vehicle_typst
from tests.approval.vehicle.e2e.test_air_raft import build_air_raft
from tests.approval.vehicle.e2e.test_atv import build_atv

from ._output import write_json_output, write_pdf_output, write_typst_output

pytestmark = pytest.mark.generated_output

_VEHICLES = sorted(
    [
        ('test_air_raft', build_air_raft),
        ('test_atv', build_atv),
    ],
    key=lambda entry: entry[1]().name.lower(),
)


@pytest.mark.parametrize(('name', 'builder'), _VEHICLES)
def test_vehicle_gallery_json_output(name: str, builder) -> None:
    output_path = write_json_output(name, builder())
    assert output_path.exists()
    assert '"tl":' in output_path.read_text(encoding='utf-8')


@pytest.mark.parametrize(('name', 'builder'), _VEHICLES)
def test_vehicle_gallery_typst_output(name: str, builder) -> None:
    source = render_vehicle_typst(builder())
    output_path = write_typst_output(name, source)
    assert output_path.exists()
    assert 'STRUCTURE' in source


@pytest.mark.parametrize(('name', 'builder'), _VEHICLES)
def test_vehicle_gallery_pdf_output(name: str, builder) -> None:
    pdf = render_vehicle_pdf(builder())
    output_path = write_pdf_output(name, pdf)
    assert output_path.exists()
    assert pdf.startswith(b'%PDF-')
