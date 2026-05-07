from dataclasses import replace

from ceres.shared import _Note

from .spec import ShipSpec, SpecRow


def collapsed_main_rows(spec: ShipSpec) -> list[SpecRow]:
    rows = [row for row in spec.rows if not (row.power is not None and row.tons is None and row.cost is None)]
    if not rows:
        return []
    rows = _collapse_repeated_blocks(rows, block_len=2)

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


def _collapse_repeated_blocks(rows: list[SpecRow], *, block_len: int) -> list[SpecRow]:
    if len(rows) < block_len * 2:
        return rows

    collapsed: list[SpecRow] = []
    index = 0
    while index < len(rows):
        block = rows[index : index + block_len]
        if len(block) < block_len:
            collapsed.extend(block)
            break

        repeat_count = 1
        next_index = index + block_len
        while next_index + block_len <= len(rows):
            next_block = rows[next_index : next_index + block_len]
            if not _blocks_match(block, next_block):
                break
            repeat_count += 1
            next_index += block_len

        if repeat_count == 1:
            collapsed.append(rows[index])
            index += 1
            continue

        for offset in range(block_len):
            merged = block[offset]
            for repetition in range(1, repeat_count):
                merged = _merge_rows(merged, rows[index + repetition * block_len + offset])
            collapsed.append(merged)
        index += repeat_count * block_len
    return collapsed


def _blocks_match(left: list[SpecRow], right: list[SpecRow]) -> bool:
    return len(left) == len(right) and all(
        _can_collapse(l_row, r_row) for l_row, r_row in zip(left, right, strict=True)
    )


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


def _copy_notes(notes: list[_Note]) -> list[_Note]:
    return list(notes)
