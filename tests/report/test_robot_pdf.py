import pytest

from ceres.make.robot.report import render_robot_spec_typst
from ceres.report import render_robot_pdf, render_robot_spec_pdf
from tests.robots.test_domestic_servant import build_domestic_servant
from tests.robots.test_lab_control_robot_basic import build_basic_lab_control_robot


@pytest.fixture
def domestic_spec():
    return build_domestic_servant().build_spec()


@pytest.fixture
def lab_spec():
    return build_basic_lab_control_robot().build_spec()


# ---------------------------------------------------------------------------
# Public API smoke tests
# ---------------------------------------------------------------------------


@pytest.mark.slow
def test_render_robot_spec_pdf_returns_pdf_bytes(domestic_spec):
    pdf = render_robot_spec_pdf(domestic_spec)
    assert pdf[:4] == b'%PDF'


@pytest.mark.slow
def test_render_robot_pdf_returns_pdf_bytes():
    pdf = render_robot_pdf(build_domestic_servant())
    assert pdf[:4] == b'%PDF'


def test_render_robot_spec_typst_page_size_passed_through(domestic_spec):
    src_a4 = render_robot_spec_typst(domestic_spec, page_size='a4')
    src_letter = render_robot_spec_typst(domestic_spec, page_size='us-letter')
    assert '"a4"' in src_a4
    assert '"us-letter"' in src_letter


# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------


def test_source_contains_robot_name_uppercased(domestic_spec):
    src = render_robot_spec_typst(domestic_spec)
    assert 'DOMESTIC SERVANT' in src


def test_source_contains_tech_level(domestic_spec):
    src = render_robot_spec_typst(domestic_spec)
    assert 'TL 8' in src


# ---------------------------------------------------------------------------
# Spec rows
# ---------------------------------------------------------------------------


def test_source_contains_section_labels(domestic_spec):
    src = render_robot_spec_typst(domestic_spec)
    for label in ('Robot', 'Skills', 'Traits', 'Programming', 'Endurance', 'Options'):
        assert label in src


def test_source_contains_row_values(domestic_spec):
    src = render_robot_spec_typst(domestic_spec)
    assert 'Hits' in src
    assert 'Wheels' in src


def test_source_contains_options_from_default_suite(domestic_spec):
    src = render_robot_spec_typst(domestic_spec)
    assert 'Auditory Sensor' in src
    assert 'Wireless Data Link' in src


def test_source_contains_skills(domestic_spec):
    src = render_robot_spec_typst(domestic_spec)
    assert 'Recon' in src


def test_source_lab_robot_substituted_suite(lab_spec):
    src = render_robot_spec_typst(lab_spec)
    assert 'Transceiver 500km (improved)' in src
    assert 'Video Screen (improved)' in src


# ---------------------------------------------------------------------------
# Notes
# ---------------------------------------------------------------------------


def test_source_renders_robot_level_notes():
    from ceres.make.robot.spec import RobotSpec, RobotSpecRow, RobotSpecSection
    from ceres.shared import NoteList

    spec = RobotSpec(name='Test Bot', tl=8)
    spec.robot_notes = NoteList()
    spec.robot_notes.error('Slot overload')
    spec.add_row(RobotSpecRow(section=RobotSpecSection.ROBOT, label='Robot', value='Hits 1'))
    src = render_robot_spec_typst(spec)
    assert 'Slot overload' in src
    assert 'gc-error(' in src
