"""Web-agnostic input descriptors for pending inputs.

The pending layer says *what it needs*; the web layer decides *how to render it*.
"""

from collections.abc import Mapping
from dataclasses import dataclass, field


@dataclass
class NumberEntry:
    """A numeric value in a range (e.g. a dice roll, a characteristic)."""

    name: str
    label: str
    min: int
    max: int


@dataclass
class Select:
    """A selection from a list of options.

    min_select == max_select == 1 → radio buttons.
    max_select > min_select → checkbox group with enforced limits.
    default: pre-selected value; None means no pre-selection.
    """

    name: str
    label: str
    options: list[tuple[str, str]] = field(default_factory=list)  # (display_label, value)
    min_select: int = 1
    max_select: int = 1
    default: str | None = None


@dataclass
class Reference:
    """A fixed value that accompanies the submission (hidden field in web)."""

    name: str
    value: str


@dataclass
class TextEntry:
    """A free-text string value (name, note, description)."""

    name: str
    label: str
    value: str = ''
    placeholder: str = ''
    multiline: bool = False


@dataclass
class InfoText:
    """Supplementary explanatory text — no input required."""

    text: str


@dataclass
class WorldRef:
    """A Traveller Map world location used as a reference point."""

    sector_abbreviation: str
    hex: str


@dataclass
class WorldFilterCriteria:
    """Initial world-picker filter values.

    Values are literal UI/domain codes. For example, TL 8-12 is represented as
    ("8", "9", "A", "B", "C"), not as a range.
    """

    allegiances: tuple[str, ...] = ()
    remarks: tuple[str, ...] = ()
    bases: tuple[str, ...] = ()
    starports: tuple[str, ...] = ()
    sizes: tuple[str, ...] = ()
    atmospheres: tuple[str, ...] = ()
    hydrographics: tuple[str, ...] = ()
    populations: tuple[str, ...] = ()
    governments: tuple[str, ...] = ()
    law_levels: tuple[str, ...] = ()
    tech_levels: tuple[str, ...] = ()


@dataclass
class SelectWorld:
    """A request for the client to let the user choose a Traveller Map world."""

    name: str
    label: str
    sector_abbreviation: str | None = None
    reference_world: WorldRef | None = None
    filters: WorldFilterCriteria = field(default_factory=WorldFilterCriteria)


@dataclass
class QualificationTarget:
    """The unmodified characteristic target for entering a career."""

    characteristic: str
    target: int


@dataclass
class AssignmentOption:
    """A selectable assignment and its player-facing description."""

    name: str
    description: str


@dataclass
class CareerOption:
    """A selectable career and the information needed to choose it."""

    name: str
    description: str
    qualification: QualificationTarget
    assignments: list[AssignmentOption]


@dataclass
class PrecareerOption:
    """A selectable pre-career education option."""

    name: str
    entry_requirement: str  # e.g. "EDU 8+" or "Automatic"
    curricula: list[str]


@dataclass
class CareerChoice:
    """Fully declarative career/pre-career selection widget.

    Carries all data needed to render the combined career and pre-career
    chooser without additional server calls.
    """

    career_options: list[CareerOption]
    precareer_options: list[PrecareerOption] = field(default_factory=list)
    can_finish: bool = False


InputSpec = NumberEntry | Select | Reference | TextEntry | InfoText | SelectWorld | CareerChoice


def form_str(form: Mapping[str, str], key: str, default: str = '') -> str:
    value = form.get(key, default)
    if not isinstance(value, str):
        return default
    return value


def form_int(form: Mapping[str, str], key: str, default: int) -> int:
    value = form_str(form, key, str(default))
    return int(value or default)


def literal(value: str, allowed: tuple[str, ...], default: str) -> str:
    if value in allowed:
        return value
    return default
