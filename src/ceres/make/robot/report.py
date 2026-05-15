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
    return {
        'name': spec.name,
        'name_upper': spec.name.upper(),
        'tl': spec.tl,
        'rows': [
            {
                'label': row.label,
                'value': row.value,
                'notes': _notes_for_display(row.notes),
            }
            for row in spec.rows
        ],
        'robot_notes': _notes_for_display(spec.robot_notes),
        'page_size': page_size,
    }


def _notes_for_display(notes: list[_Note]) -> list[dict]:
    return NoteList(notes).detail_entries
