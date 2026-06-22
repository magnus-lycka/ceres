"""Draft table construction and alternative lookup (RIC-003)."""

from collections.abc import Iterable

from ceres.character.domain.career.career_data import CareerData


def build_draft_table(summary, careers: Iterable[CareerData]) -> list[CareerData]:
    """Return careers in the draft, sorted by (weight, name).

    Each career's is_in_draft(summary) returns 0 (not draftable) or a positive
    weight.  Careers with equal weight are ordered alphabetically.
    """
    weighted = [(c.is_in_draft(summary), c) for c in careers]
    draftable = [(w, c) for w, c in weighted if w > 0]
    return [c for _, c in sorted(draftable, key=lambda wc: (wc[0], wc[1].name))]


def get_draft_alternative(summary, careers: Iterable[CareerData]) -> CareerData | None:
    """Return the first career offering itself as a draft alternative, or None."""
    return next((c for c in careers if c.is_draft_alternative(summary)), None)
