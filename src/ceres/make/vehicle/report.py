"""Vehicle report rendering — building the context and calling the engine.

The spec carries values; this is where they become the strings a stat block
prints, such as 'High (Medium)' and 'Cr155000'.
"""

from dataclasses import asdict, dataclass
from pathlib import Path

from ceres.shared import NoteList, _Note

from .spec import EquipmentSpec, VehicleSpec
from .vehicle import Vehicle

_TEMPLATES = Path(__file__).parent / 'templates'

_DASH = '—'


def _credits(amount: float) -> str:
    return f'Cr{amount:,.0f}'


def _paired(maximum, cruise) -> str:
    """A stat block prints the maximum with the cruising figure in parentheses."""
    if maximum is None:
        return _DASH
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
        ('CREW, PASSENGERS', f'{spec.crew}, {spec.passengers}'),
        ('COMFORT LEVEL', spec.comfort_label or _DASH),
        ('CARGO', f'{spec.cargo_tons:,g} tons'),
        ('STRUCTURE', str(spec.structure)),
        ('SHIPPING', f'{spec.shipping_tons:,g} tons'),
        ('COST', _credits(spec.cost)),
    ]
    return [{'label': label, 'value': value} for label, value in rows]


def _km(distance: int | None) -> str | None:
    return None if distance is None else f'{distance:,}'


def _armour_rows(spec: VehicleSpec) -> list[dict]:
    """Each face's Protection, with the small-arms figure in parentheses (RIV-003).

    A face without the Tech Level bonus prints its Protection alone, and one with
    no protection at all — an open top — prints a dash, as the catalogue does.
    """
    rows = []
    for face, protection in spec.armour.items():
        against_small_arms = spec.armour_against_small_arms[face]
        if against_small_arms > protection:
            value = f'{protection} ({against_small_arms})'
        else:
            value = str(protection) if protection else _DASH
        rows.append({'face': face.value, 'value': value})
    return rows


def _signed(value: int | None) -> str:
    """A modifier as the catalogue prints it, or a dash where there is none."""
    return _DASH if value is None else f'{value:+d}'


def _communications(spec: VehicleSpec) -> str:
    comms = spec.communications
    if comms is None:
        return _DASH
    words = [f'{comms.range_km}km']
    words += [
        word
        for flag, word in (
            (comms.tightbeam, 'tightbeam'),
            (comms.satellite_uplink, 'satellite uplink'),
            (comms.encryption, 'encrypted'),
        )
        if flag
    ]
    return ', '.join(words)


def _derived_figure_rows(spec: VehicleSpec) -> list[dict]:
    """The small table beneath the equipment list. Every row is always present."""
    sensors = _DASH if spec.sensors_dm is None else f'{spec.sensors_dm:+d}, {spec.sensors_range_km}km'
    rows = [
        ('Autopilot (skill level)', _signed(spec.autopilot_skill)),
        ('Communications (range)', _communications(spec)),
        ('Navigation (Navigation DM)', _signed(spec.navigation_dm)),
        ('Sensors (Electronics (sensors) DM)', sensors),
        # Neither is modelled yet, so every design prints the dash the catalogue
        # prints for one that carries none.
        ('Camouflage (Recon DM)', _DASH),
        ('Stealth (Electronics (sensors) DM)', _DASH),
    ]
    return [{'label': label, 'value': value} for label, value in rows]


def _equipment_label(item: EquipmentSpec) -> str:
    """An item as the catalogue lists it: 'Collision Protection (improved) x16',
    'Fusion+ (basic) PP 2', 'Aquatic Drive (Very Slow, 600km)'."""
    label = item.name
    if item.speed is not None:
        label += f' ({item.speed}, {item.range_km:,}km)'
    elif item.grade is not None:
        label += f' ({item.grade})'
    if item.power_points is not None:
        label += f' PP {item.power_points}'
    if item.quantity > 1:
        label += f' x{item.quantity}'
    return label


@dataclass(frozen=True)
class _WeaponRow:
    """One row of the Weapons table. An empty mount has only its own description."""

    weapon: str
    range: str = _DASH
    damage: str = _DASH
    magazine: str = _DASH
    cost: str = _DASH
    traits: str = _DASH
    fire_control: str = _DASH


def _weapon_rows(spec: VehicleSpec) -> list[dict]:
    """The Weapons table. An empty mount prints its capacity and dashes elsewhere."""
    return [
        asdict(
            _WeaponRow(weapon=f'{mount.mount}: {mount.face.value}, can hold {mount.weapon_spaces} Spaces of weapons')
        )
        for mount in spec.mounts
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
        'weapons': _weapon_rows(spec),
        'equipment': sorted(_equipment_label(item) for item in spec.equipment),
        'derived_figures': _derived_figure_rows(spec),
        'notes': _notes_for_display(spec.notes),
        'image': image,
        'page_size': page_size,
    }


def _notes_for_display(notes: list[_Note]) -> list[dict]:
    return NoteList(notes).detail_entries
