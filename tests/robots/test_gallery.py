import pytest

from ceres.make.robot.report import render_robot_typst
from ceres.report import render_robot_pdf

from ._output import write_json_output, write_pdf_output, write_typst_output
from .test_ag300 import build_ag300
from .test_basic_courier import build_basic_courier
from .test_domestic_servant import build_domestic_servant
from .test_lab_control_robot_advanced import build_advanced_lab_control_robot
from .test_lab_control_robot_basic import build_basic_lab_control_robot
from .test_utility_droid import build_utility_droid

pytestmark = pytest.mark.generated_output

_ROBOTS = [
    ('test_ag300', build_ag300),
    ('test_basic_courier', build_basic_courier),
    ('test_domestic_servant', build_domestic_servant),
    ('test_lab_control_robot_advanced', build_advanced_lab_control_robot),
    ('test_lab_control_robot_basic', build_basic_lab_control_robot),
    ('test_utility_droid', build_utility_droid),
]


@pytest.mark.parametrize(('name', 'builder'), _ROBOTS)
def test_robot_gallery_json_output(name: str, builder) -> None:
    robot = builder()
    output_path = write_json_output(name, robot)
    assert output_path.exists()
    assert '"tl":' in output_path.read_text(encoding='utf-8')


@pytest.mark.parametrize(('name', 'builder'), _ROBOTS)
def test_robot_gallery_typst_output(name: str, builder) -> None:
    robot = builder()
    typst_src = render_robot_typst(robot)
    output_path = write_typst_output(name, typst_src)
    assert output_path.exists()
    assert 'report_data' in output_path.read_text(encoding='utf-8')


@pytest.mark.slow
@pytest.mark.parametrize(('name', 'builder'), _ROBOTS)
def test_robot_gallery_pdf_output(name: str, builder) -> None:
    robot = builder()
    pdf_bytes = render_robot_pdf(robot)
    output_path = write_pdf_output(name, pdf_bytes)
    assert output_path.exists()
    assert pdf_bytes[:4] == b'%PDF'
