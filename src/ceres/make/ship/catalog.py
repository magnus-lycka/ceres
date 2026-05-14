"""Ship computer/core catalog — builds report context and renders HTML/PDF."""

from pathlib import Path
from typing import Literal

from ceres.report.render import render_html, render_pdf, render_typst_source

from .computer import (
    Computer5,
    Computer10,
    Computer15,
    Computer20,
    Computer25,
    Computer30,
    Computer35,
    ComputerBase,
    Core40,
    Core50,
    Core60,
    Core70,
    Core80,
    Core90,
    Core100,
)

ReportTheme = Literal['light', 'dark']

_GEAR_TEMPLATES = Path(__file__).parent.parent.parent / 'gear' / 'templates'

_COMPUTERS: list[ComputerBase] = [
    Computer5(),
    Computer10(),
    Computer15(),
    Computer20(),
    Computer25(),
    Computer30(),
    Computer35(),
]
_CORES: list[ComputerBase] = [
    Core40(),
    Core50(),
    Core60(),
    Core70(),
    Core80(),
    Core90(),
    Core100(),
]


def _fmt_mcr(cost: float) -> str:
    if cost < 1_000_000:
        return f'kCr{cost / 1_000:,.3f}'
    return f'MCr{cost / 1_000_000:,.3f}'


_HEADERS = ['Processing', 'TL', 'Cost', 'BIS', 'FIB', 'BIS+FIB']
_ALIGNMENTS = ['left', 'right', 'right', 'right', 'right', 'right']


def _cost_row(c: ComputerBase, display_tl: int) -> dict:
    base = c.base_cost
    return {
        'cells': [
            str(c.processing),
            str(display_tl),
            _fmt_mcr(base),
            _fmt_mcr(base * 1.5),
            _fmt_mcr(base * 1.5),
            _fmt_mcr(base * 2.0),
        ],
        'notes': [],
    }


def _computer_section(instances: list[ComputerBase], heading: str) -> dict:
    rows = [_cost_row(c, c.tl) for c in instances]
    return {'heading': heading, 'headers': _HEADERS, 'alignments': _ALIGNMENTS, 'rows': rows}


def _retro_section(instances: list[ComputerBase], heading: str) -> dict:
    rows = []
    for ship_tl in range(8, 17):
        for c in instances:
            if c.tl < ship_tl:
                retro = c.model_copy(update={'retro_levels': ship_tl - c.tl})
                rows.append(_cost_row(retro, ship_tl))
    return {'heading': f'Retro {heading}', 'headers': _HEADERS, 'alignments': _ALIGNMENTS, 'rows': rows}


def _proto_section(instances: list[ComputerBase], heading: str) -> dict:
    rows = []
    for proto_levels in range(1, 3):
        for c in instances:
            ship_tl = c.tl - proto_levels
            if ship_tl >= 4:
                proto = c.model_copy(update={'proto_levels': proto_levels})
                rows.append(_cost_row(proto, ship_tl))
    return {'heading': f'Proto {heading}', 'headers': _HEADERS, 'alignments': _ALIGNMENTS, 'rows': rows}


def _build_context(*, theme: ReportTheme = 'light', page_size: str = 'a4') -> dict:
    return {
        'title': 'Ship Computers',
        'eyebrow': 'High Guard',
        'theme': theme,
        'page_size': page_size,
        'sections': [
            _computer_section(_COMPUTERS, 'Computer'),
            _computer_section(_CORES, 'Core'),
            _retro_section(_COMPUTERS, 'Computer'),
            _retro_section(_CORES, 'Core'),
            _proto_section(_COMPUTERS, 'Computer'),
            _proto_section(_CORES, 'Core'),
        ],
    }


def render_ship_computer_catalog_html(*, theme: ReportTheme = 'light') -> str:
    return render_html(_GEAR_TEMPLATES / 'computer_catalog.html.j2', _build_context(theme=theme))


def render_ship_computer_catalog_typst(*, page_size: str = 'a4') -> str:
    return render_typst_source(_GEAR_TEMPLATES / 'computer_catalog.typ', _build_context(page_size=page_size))


def render_ship_computer_catalog_pdf(*, page_size: str = 'a4') -> bytes:
    return render_pdf(_GEAR_TEMPLATES / 'computer_catalog.typ', _build_context(page_size=page_size))
