from collections.abc import Iterable


def format_counted_label(label: str, count: int | None) -> str:
    if count is None or count <= 1:
        return label
    return f'{label} × {count}'


def optional_count(count: int) -> int | None:
    if count <= 1:
        return None
    return count


def collapse_repeated_labels(labels: Iterable[str]) -> list[str]:
    counts: dict[str, int] = {}
    order: list[str] = []
    for label in labels:
        if label not in counts:
            order.append(label)
            counts[label] = 0
        counts[label] += 1
    return [format_counted_label(label, counts[label]) for label in order]
