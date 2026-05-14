"""Computer equipment catalog — builds report context and renders HTML/PDF."""

from pathlib import Path
from typing import Literal

from ceres.report.render import render_html, render_pdf, render_typst_source
from ceres.shared import NoteList

from .computer import (
    ComputerChip,
    ComputerEquipment,
    ComputerTerminal,
    InterfaceDevice,
    MainframeComputer,
    MicroscopicChip,
    MidSizedComputer,
    PortableComputer,
    SpecialisedComputer,
    SpecialisedTablet,
    Tablet,
)
from .software import Expert

ReportTheme = Literal['light', 'dark']

__all__ = ['render_computer_catalog_html', 'render_computer_catalog_pdf', 'render_computer_catalog_typst']

_TEMPLATES = Path(__file__).parent / 'templates'

_COMPUTER_TYPES: list[type[ComputerEquipment]] = [
    ComputerTerminal,
    InterfaceDevice,
    MainframeComputer,
    MidSizedComputer,
    PortableComputer,
    Tablet,
    ComputerChip,
    MicroscopicChip,
]

_SPECIALISED_EXAMPLES: list[SpecialisedComputer] = [
    SpecialisedComputer(processing=1, expert=Expert(rating=1, skill='Admin'), variant='intelligent_interface'),
    SpecialisedComputer(processing=2, expert=Expert(rating=2, skill='Astrogation'), variant='intelligent_interface'),
    SpecialisedComputer(processing=1, expert=Expert(rating=1, skill='Medic'), variant='intelligent_interface'),
    SpecialisedTablet(processing=1, expert=Expert(rating=1, skill='Steward'), variant='intelligent_interface'),
    SpecialisedTablet(processing=2, expert=Expert(rating=2, skill='Medic'), variant='intelligent_interface'),
    SpecialisedComputer(processing=3, expert=Expert(rating=3, skill='Broker'), variant='intellect'),
    SpecialisedComputer(processing=2, expert=Expert(rating=2, skill='Engineer (M-Drive)'), variant='intellect'),
    SpecialisedTablet(processing=2, expert=Expert(rating=2, skill='Broker'), variant='intellect'),
]


def _fmt_cost(cost: float) -> str:
    if cost < 1:
        return f'Cr{cost:.2f}'
    return f'Cr{cost:,.0f}'


def _fmt_mass(mass: float) -> str:
    return f'{round(mass, 3):g}' if mass > 0 else '—'


def _notes_for_display(item) -> list[dict]:
    return NoteList(getattr(item, 'notes', [])).detail_entries


def _standard_section(cls: type[ComputerEquipment]) -> dict:
    rows = []
    for p in sorted(cls._specs):
        item = cls(processing=p)
        rows.append(
            {
                'cells': [str(p), str(item.tl), _fmt_mass(item.mass_kg), _fmt_cost(item.cost)],
                'notes': _notes_for_display(item),
            }
        )
    return {
        'heading': cls(processing=min(cls._specs))._label,
        'headers': ['Processing', 'TL', 'Mass (kg)', 'Cost'],
        'alignments': ['left', 'right', 'right', 'right'],
        'rows': rows,
    }


def _retro_section(cls: type[ComputerEquipment]) -> dict:
    rows = []
    for tl in range(7, 17):
        for p in sorted(cls._specs):
            item = cls(processing=p)
            if item.tl < tl:
                item = cls(processing=p, tl=tl)
                rows.append(
                    {
                        'cells': [str(p), str(tl), _fmt_mass(item.mass_kg), _fmt_cost(item.cost)],
                        'notes': _notes_for_display(item),
                    }
                )
    return {
        'heading': 'Retrotech ' + cls(processing=min(cls._specs))._label,
        'headers': ['Processing', 'TL', 'Mass (kg)', 'Cost'],
        'alignments': ['left', 'right', 'right', 'right'],
        'rows': rows,
    }


def _proto_section(cls: type[ComputerEquipment]) -> dict:
    rows = []
    for tl in range(4, 15):
        for p in sorted(cls._specs):
            item = cls(processing=p)
            if item.tl > tl and item.tl < tl + 3:
                item = cls(processing=p, tl=tl)
                rows.append(
                    {
                        'cells': [str(p), str(tl), _fmt_mass(item.mass_kg), _fmt_cost(item.cost)],
                        'notes': _notes_for_display(item),
                    }
                )
    return {
        'heading': 'Prototech ' + cls(processing=min(cls._specs))._label,
        'headers': ['Processing', 'TL', 'Mass (kg)', 'Cost'],
        'alignments': ['left', 'right', 'right', 'right'],
        'rows': rows,
    }


def _specialised_section() -> dict:
    rows = []
    for sc in _SPECIALISED_EXAMPLES:
        name = sc.notes[0].message if sc.notes else ''
        rows.append(
            {
                'cells': [name, _fmt_mass(sc.mass_kg), str(sc.tl), _fmt_cost(sc.cost)],
                'notes': _notes_for_display(sc),
            }
        )
    return {
        'heading': 'Specialised Computer (examples)',
        'headers': ['Item', 'Mass (kg)', 'TL', 'Cost'],
        'alignments': ['left', 'right', 'right', 'right'],
        'rows': rows,
    }


def _build_context(*, theme: ReportTheme = 'light', page_size: str = 'a4') -> dict:
    sections = [_standard_section(cls) for cls in _COMPUTER_TYPES]
    sections.extend(_retro_section(cls) for cls in _COMPUTER_TYPES if cls._allow_retro)
    sections.extend(_proto_section(cls) for cls in _COMPUTER_TYPES if cls._allow_proto)
    sections.append(_specialised_section())
    return {
        'title': 'Computer Equipment',
        'eyebrow': 'Central Supply Catalogue',
        'theme': theme,
        'page_size': page_size,
        'sections': sections,
    }


def render_computer_catalog_html(*, theme: ReportTheme = 'light') -> str:
    return render_html(_TEMPLATES / 'computer_catalog.html.j2', _build_context(theme=theme))


def render_computer_catalog_typst(*, page_size: str = 'a4') -> str:
    return render_typst_source(_TEMPLATES / 'computer_catalog.typ', _build_context(page_size=page_size))


def render_computer_catalog_pdf(*, page_size: str = 'a4') -> bytes:
    return render_pdf(_TEMPLATES / 'computer_catalog.typ', _build_context(page_size=page_size))
