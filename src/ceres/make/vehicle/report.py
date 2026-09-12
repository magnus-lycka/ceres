"""Vehicle report rendering — building the context and calling the engine.

The spec carries values; this is where they become the strings a stat block
prints, such as 'High (Medium)' and 'Cr155000'.
"""

from pathlib import Path

from ceres.shared import NoteList, _Note

from .spec import VehicleSpec
from .vehicle import Vehicle

_TEMPLATES = Path(__file__).parent / 'templates'


def _credits(amount: float) -> str:
    return f'Cr{amount:,.0f}'


def _paired(maximum, cruise) -> str:
    """A stat block prints the maximum with the cruising figure in parentheses."""
    if maximum is None:
        return '—'
    if cruise is None:
        return str(maximum)
    return f'{maximum} ({cruise})'


def _type_line(spec: VehicleSpec) -> str:
    return f'{spec.size.value} {spec.vehicle_type.value} ({spec.spaces:,} Spaces, DM{spec.target_size_dm:+d} to hit)'


def _stat_rows(spec: VehicleSpec) -> list[dict]:
    """The main table, in the order the catalogue prints it.

    Rows the design cannot yet produce are simply absent.
    """
    rows = [
        ('TL', str(spec.tl)),
        ('SKILL', spec.skill),
        ('AGILITY', f'{spec.agility:+d}'),
        ('SPEED (CRUISE)', _paired(spec.speed, spec.cruise_speed)),
        ('RANGE (CRUISE)', _paired(_km(spec.range_km), _km(spec.cruise_range_km))),
        ('STRUCTURE', str(spec.structure)),
        ('SHIPPING', f'{spec.shipping_tons:,g} tons'),
        ('COST', _credits(spec.cost)),
    ]
    return [{'label': label, 'value': value} for label, value in rows]


def _km(distance: int | None) -> str | None:
    return None if distance is None else f'{distance:,}'


def _armour_rows(spec: VehicleSpec) -> list[dict]:
    """Each face's Protection, with the small-arms figure in parentheses.

    The parenthesised figure is composed here and stored nowhere (RIV-003).
    """
    return [
        {'face': face.value, 'value': f'{protection} ({protection + spec.tl})'}
        for face, protection in spec.armour.items()
    ]


def render_vehicle_typst(vehicle: Vehicle, *, page_size: str = 'a4', image: str | None = None) -> str:
    return render_vehicle_spec_typst(vehicle.build_spec(), page_size=page_size, image=image)


def render_vehicle_spec_typst(spec: VehicleSpec, *, page_size: str = 'a4', image: str | None = None) -> str:
    from ceres.report.render import render_typst_source  # noqa: PLC0415

    return render_typst_source(_TEMPLATES / 'vehicle_spec.typ', _build_context(spec, page_size=page_size, image=image))


def render_vehicle_pdf(vehicle: Vehicle, *, page_size: str = 'a4', image: str | None = None) -> bytes:
    return render_vehicle_spec_pdf(vehicle.build_spec(), page_size=page_size, image=image)


def render_vehicle_spec_pdf(spec: VehicleSpec, *, page_size: str = 'a4', image: str | None = None) -> bytes:
    from ceres.report.render import render_pdf  # noqa: PLC0415

    return render_pdf(_TEMPLATES / 'vehicle_spec.typ', _build_context(spec, page_size=page_size, image=image))


def _build_context(spec: VehicleSpec, *, page_size: str = 'a4', image: str | None = None) -> dict:
    return {
        'name': spec.name,
        'name_upper': spec.name.upper(),
        'description': spec.description,
        'type_line': _type_line(spec),
        'features_and_traits': ', '.join(spec.features_and_traits) or 'None',
        'stats': _stat_rows(spec),
        'armour': _armour_rows(spec),
        'notes': _notes_for_display(spec.notes),
        'image': image,
        'page_size': page_size,
    }


def _notes_for_display(notes: list[_Note]) -> list[dict]:
    return NoteList(notes).detail_entries
