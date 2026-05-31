"""Web-agnostic input descriptors for pending inputs.

The pending layer says *what it needs*; the web layer decides *how to render it*.
"""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class NumberEntry:
    """A numeric value in a range (e.g. a dice roll, a characteristic)."""

    name: str
    label: str
    default: int
    min: int
    max: int


@dataclass
class Select:
    """A selection from a list of options.

    min_select == max_select == 1 → radio buttons.
    max_select > min_select → checkbox group with enforced limits.
    """

    name: str
    label: str
    options: list[tuple[str, str]] = field(default_factory=list)  # (display_label, value)
    min_select: int = 1
    max_select: int = 1


@dataclass
class Reference:
    """A fixed value that accompanies the submission (hidden field in web)."""

    name: str
    value: str


@dataclass
class InfoText:
    """Supplementary explanatory text — no input required."""

    text: str


InputSpec = NumberEntry | Select | Reference | InfoText


def form_str(form: Any, key: str, default: str = '') -> str:
    value = form.get(key, default)
    if not isinstance(value, str):
        return default
    return value


def form_int(form: Any, key: str, default: int) -> int:
    value = form_str(form, key, str(default))
    return int(value or default)


def literal(value: str, allowed: tuple[str, ...], default: str) -> str:
    if value in allowed:
        return value
    return default
