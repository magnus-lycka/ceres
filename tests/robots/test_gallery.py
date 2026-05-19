import inspect

import pytest

from ceres.make.robot.report import render_robot_typst
from ceres.report import render_pdf_source

from ._output import write_json_output, write_pdf_output, write_typst_output
from .test_ag300 import build_ag300
from .test_basic_courier import build_basic_courier
from .test_domestic_servant import build_domestic_servant
from .test_gardener_servant import build_gardener_servant
from .test_gonzales import build_gonzales
from .test_hudson import build_hudson
from .test_hush import build_hush
from .test_lab_control_robot_advanced import build_advanced_lab_control_robot
from .test_lab_control_robot_basic import build_basic_lab_control_robot
from .test_mimer import build_mimer
from .test_rhino import build_rhino
from .test_startek import build_startek_fuller as build_startek
from .test_utility_droid import build_utility_droid
from .test_wush import build_wush

pytestmark = pytest.mark.generated_output

_ROBOTS = sorted(
    [
        ('test_ag300', build_ag300),
        ('test_basic_courier', build_basic_courier),
        ('test_domestic_servant', build_domestic_servant),
        ('test_gardener_servant', build_gardener_servant),
        ('test_gonzales', build_gonzales),
        ('test_hudson', build_hudson),
        ('test_hush', build_hush),
        ('test_lab_control_robot_advanced', build_advanced_lab_control_robot),
        ('test_lab_control_robot_basic', build_basic_lab_control_robot),
        ('test_mimer', build_mimer),
        ('test_rhino', build_rhino),
        ('test_startek', build_startek),
        ('test_utility_droid', build_utility_droid),
        ('test_wush', build_wush),
    ],
    key=lambda entry: entry[1]().name,
)


@pytest.mark.parametrize(('name', 'builder'), _ROBOTS)
def test_robot_gallery_json_output(name: str, builder) -> None:
    robot = builder()
    output_path = write_json_output(name, robot)
    assert output_path.exists()
    assert '"tl":' in output_path.read_text(encoding='utf-8')


def _builder_note(builder) -> str | None:
    doc = inspect.cleandoc(builder.__doc__ or '')
    return doc if doc.startswith('Note:') else None


@pytest.mark.parametrize(('name', 'builder'), _ROBOTS)
def test_robot_gallery_typst_output(name: str, builder) -> None:
    robot = builder()
    typst_src = render_robot_typst(robot, note=_builder_note(builder))
    output_path = write_typst_output(name, typst_src)
    assert output_path.exists()
    assert 'report_data' in output_path.read_text(encoding='utf-8')


def _render_robot_gallery_typst() -> str:
    return '\n#pagebreak()\n'.join(
        render_robot_typst(builder(), note=_builder_note(builder)) for _name, builder in _ROBOTS
    )


@pytest.mark.slow
def test_robot_gallery_pdf_output() -> None:
    typst_src = _render_robot_gallery_typst()
    typst_output_path = write_typst_output('robots_gallery', typst_src)
    pdf_bytes = render_pdf_source(typst_src)
    output_path = write_pdf_output('robots_gallery', pdf_bytes)

    assert typst_output_path.exists()
    assert output_path.exists()
    assert pdf_bytes[:4] == b'%PDF'
