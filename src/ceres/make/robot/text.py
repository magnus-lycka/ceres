from .chassis import Trait


def format_traits(traits: list[Trait]) -> str:
    return ', '.join(str(t) for t in traits) if traits else '—'


def format_credits(amount: float) -> str:
    if amount >= 1_000_000:
        return f'MCr{amount / 1_000_000:g}'
    return f'Cr{int(amount):,}'


__all__ = ['format_traits', 'format_credits']
