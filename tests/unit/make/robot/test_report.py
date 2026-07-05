"""Unit tests for robot report rendering."""

from typing import cast

import pytest

from ceres.make.robot import report
from ceres.make.robot.robot import Robot
from ceres.make.robot.spec import RobotDetailRow, RobotDetailSection, RobotSpec, RobotSpecRow, RobotSpecSection
from ceres.shared import NoteList


class _Robot:
    def __init__(self, spec: RobotSpec):
        self._spec = spec

    def build_spec(self) -> RobotSpec:
        return self._spec


def _spec() -> RobotSpec:
    spec = RobotSpec(name='Helpful Bot', tl=12)
    spec.robot_notes.info('robot note')
    row_notes = NoteList()
    row_notes.item('hidden item note')
    row_notes.info('visible info')
    row_notes.error('visible error')
    spec.add_row(
        RobotSpecRow(
            section=RobotSpecSection.ROBOT,
            label='Robot',
            columns=[
                ('Model', 'Domestic Servant'),
                ('Size', '3'),
                ('Hits', '12'),
                ('TL', '12'),
                ('Cost', 'Cr10,000'),
            ],
        )
    )
    spec.add_row(RobotSpecRow(section=RobotSpecSection.SKILLS, label='Skills', value='Admin 0', notes=row_notes))
    spec.add_row(RobotSpecRow(section=RobotSpecSection.OPTIONS, label='Options', value='None'))
    spec.detail_sections.append(
        RobotDetailSection(
            title='Installed Software',
            col2_header='Slots',
            col3_header='Bandwidth',
            rows=[RobotDetailRow(name='Admin', col2='—', col3='0', cost='Cr100')],
        )
    )
    return spec


def test_robot_column_widths_make_narrow_columns_half_width_and_give_savings_to_first_column():
    assert report._robot_column_widths([('Model', 'A'), ('Size', '3'), ('Hits', '12'), ('Cost', 'Cr100')]) == [
        ['Model', 'A', 2.0],
        ['Size', '3', 0.5],
        ['Hits', '12', 0.5],
        ['Cost', 'Cr100', 1.0],
    ]


def test_build_context_extracts_robot_columns_rows_details_and_notes():
    context = report._build_context(_spec(), page_size='letter', note='draft')

    assert context['name'] == 'Helpful Bot'
    assert context['name_upper'] == 'HELPFUL BOT'
    assert context['tl'] == 12
    assert context['page_size'] == 'letter'
    assert context['note'] == 'draft'
    assert context['robot_columns'][0] == ['Model', 'Domestic Servant', 2.5]
    assert [row['label'] for row in context['rows']] == ['Skills', 'Options']
    assert context['rows'][0]['notes'] == [
        {'category': 'info', 'message': 'visible info'},
        {'category': 'error', 'message': 'visible error'},
    ]
    assert context['detail_sections'] == [
        {
            'title': 'Installed Software',
            'col2_header': 'Slots',
            'col3_header': 'Bandwidth',
            'rows': [{'name': 'Admin', 'col2': '—', 'col3': '0', 'cost': 'Cr100'}],
        }
    ]
    assert context['robot_notes'] == [{'category': 'info', 'message': 'robot note'}]


def test_build_context_without_robot_column_row_uses_empty_columns():
    spec = RobotSpec(name='No Columns', tl=8)
    spec.add_row(RobotSpecRow(section=RobotSpecSection.SKILLS, label='Skills', value='—'))

    context = report._build_context(spec)

    assert context['robot_columns'] == []
    assert context['rows'] == [{'label': 'Skills', 'value': '—', 'notes': []}]


def test_render_robot_spec_typst_delegates_to_renderer(monkeypatch):
    calls = []

    def fake_render_typst_source(template, context):
        calls.append((template, context))
        return 'typst source'

    monkeypatch.setattr('ceres.report.render.render_typst_source', fake_render_typst_source)

    assert report.render_robot_spec_typst(_spec(), page_size='a5', note='preview') == 'typst source'
    template, context = calls[0]
    assert template.name == 'robot_spec.typ'
    assert context['page_size'] == 'a5'
    assert context['note'] == 'preview'


def test_render_robot_typst_builds_spec_from_robot(monkeypatch):
    captured = []

    def fake_render_robot_spec_typst(spec, *, page_size='a4', note=None):
        captured.append((spec, page_size, note))
        return 'robot typst'

    spec = _spec()
    monkeypatch.setattr(report, 'render_robot_spec_typst', fake_render_robot_spec_typst)

    assert report.render_robot_typst(cast(Robot, _Robot(spec)), page_size='letter', note='robot note') == 'robot typst'
    assert captured == [(spec, 'letter', 'robot note')]


def test_render_robot_spec_pdf_delegates_to_renderer(monkeypatch):
    calls = []

    def fake_render_pdf(template, context):
        calls.append((template, context))
        return b'%PDF'

    monkeypatch.setattr('ceres.report.render.render_pdf', fake_render_pdf)

    assert report.render_robot_spec_pdf(_spec(), page_size='a5', note='final') == b'%PDF'
    template, context = calls[0]
    assert template.name == 'robot_spec.typ'
    assert context['page_size'] == 'a5'
    assert context['note'] == 'final'


def test_render_robot_pdf_builds_spec_from_robot(monkeypatch):
    captured = []

    def fake_render_robot_spec_pdf(spec, *, page_size='a4', note=None):
        captured.append((spec, page_size, note))
        return b'%PDF'

    spec = _spec()
    monkeypatch.setattr(report, 'render_robot_spec_pdf', fake_render_robot_spec_pdf)

    assert report.render_robot_pdf(cast(Robot, _Robot(spec)), page_size='letter', note='robot note') == b'%PDF'
    assert captured == [(spec, 'letter', 'robot note')]


@pytest.mark.slow
def test_render_robot_spec_pdf_returns_pdf_bytes():
    from ceres.make.robot.report import render_robot_spec_pdf
    from tests.approval.robot.e2e.test_domestic_servant import build_domestic_servant

    pdf = render_robot_spec_pdf(build_domestic_servant().build_spec())
    assert pdf[:4] == b'%PDF'


@pytest.mark.slow
def test_render_robot_pdf_returns_pdf_bytes():
    from ceres.make.robot.report import render_robot_pdf
    from tests.approval.robot.e2e.test_domestic_servant import build_domestic_servant

    pdf = render_robot_pdf(build_domestic_servant())
    assert pdf[:4] == b'%PDF'
