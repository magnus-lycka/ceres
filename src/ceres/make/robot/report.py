"""Robot report rendering — domain logic for building context and calling the engine."""

from pathlib import Path

from ceres.make.robot.robot import Robot
from ceres.make.robot.spec import RobotSpec
from ceres.shared import NoteList, _Note

__all__ = [
    'render_robot_pdf',
    'render_robot_spec_pdf',
    'render_robot_spec_typst',
    'render_robot_typst',
]

_TEMPLATES = Path(__file__).parent / 'templates'

_NARROW_COLUMNS = frozenset({'Size', 'Hits', 'Speed', 'TL'})


def _robot_column_widths(columns: list[tuple[str, str]]) -> list[list]:
    """Assign widths: narrow columns get 0.5fr; first column absorbs the saved space."""
    narrow_count = sum(1 for h, _ in columns if h in _NARROW_COLUMNS)
    saved = narrow_count * 0.5  # each narrow column halves its 1fr default
    widths = []
    first = True
    for h, v in columns:
        if first:
            widths.append([h, v, 1.0 + saved])
            first = False
        else:
            widths.append([h, v, 0.5 if h in _NARROW_COLUMNS else 1.0])
    return widths


def render_robot_pdf(robot: Robot, *, page_size: str = 'a4') -> bytes:
    return render_robot_spec_pdf(robot.build_spec(), page_size=page_size)


def render_robot_spec_pdf(spec: RobotSpec, *, page_size: str = 'a4') -> bytes:
    from ceres.report.render import render_pdf

    return render_pdf(_TEMPLATES / 'robot_spec.typ', _build_context(spec, page_size=page_size))


def render_robot_typst(robot: Robot, *, page_size: str = 'a4') -> str:
    return render_robot_spec_typst(robot.build_spec(), page_size=page_size)


def render_robot_spec_typst(spec: RobotSpec, *, page_size: str = 'a4') -> str:
    from ceres.report.render import render_typst_source

    return render_typst_source(_TEMPLATES / 'robot_spec.typ', _build_context(spec, page_size=page_size))


def _build_context(spec: RobotSpec, *, page_size: str = 'a4') -> dict:
    from ceres.make.robot.spec import RobotSpecSection

    robot_row = next(
        (row for row in spec.rows if row.section is RobotSpecSection.ROBOT and row.columns),
        None,
    )
    other_rows = [row for row in spec.rows if not (row.section is RobotSpecSection.ROBOT and row.columns)]

    return {
        'name': spec.name,
        'name_upper': spec.name.upper(),
        'tl': spec.tl,
        'robot_columns': _robot_column_widths(robot_row.columns) if robot_row else [],
        'rows': [
            {
                'label': row.label,
                'value': row.value,
                'notes': _notes_for_display(row.notes),
            }
            for row in other_rows
        ],
        'detail_sections': [
            {
                'title': sec.title,
                'col2_header': sec.col2_header,
                'col3_header': sec.col3_header,
                'rows': [{'name': r.name, 'col2': r.col2, 'col3': r.col3, 'cost': r.cost} for r in sec.rows],
            }
            for sec in spec.detail_sections
        ],
        'robot_notes': _notes_for_display(spec.robot_notes),
        'page_size': page_size,
    }


def _notes_for_display(notes: list[_Note]) -> list[dict]:
    return NoteList(notes).detail_entries
