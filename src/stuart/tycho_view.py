from dataclasses import replace

from tycho.base import Note
from tycho.spec import ShipSpec, SpecRow


def collapsed_main_rows(spec: ShipSpec) -> list[SpecRow]:
    rows = [row for row in spec.rows if not (row.power is not None and row.tons is None and row.cost is None)]
    if not rows:
        return []

    collapsed: list[SpecRow] = []
    current = rows[0]
    for row in rows[1:]:
        if _can_collapse(current, row):
            current = _merge_rows(current, row)
            continue
        collapsed.append(current)
        current = row
    collapsed.append(current)
    return collapsed


def _can_collapse(left: SpecRow, right: SpecRow) -> bool:
    return (
        left.section == right.section
        and left.item == right.item
        and left.notes == right.notes
        and left.emphasize_tons == right.emphasize_tons
        and left.emphasize_power == right.emphasize_power
    )


def _merge_rows(left: SpecRow, right: SpecRow) -> SpecRow:
    left_qty = left.quantity or 1
    right_qty = right.quantity or 1
    return replace(
        left,
        quantity=left_qty + right_qty,
        tons=_sum_or_none(left.tons, right.tons),
        power=_sum_or_none(left.power, right.power),
        cost=_sum_or_none(left.cost, right.cost),
        notes=_copy_notes(left.notes),
    )


def _sum_or_none(left: float | None, right: float | None) -> float | None:
    if left is None and right is None:
        return None
    return (left or 0.0) + (right or 0.0)


def _copy_notes(notes: list[Note]) -> list[Note]:
    return list(notes)
