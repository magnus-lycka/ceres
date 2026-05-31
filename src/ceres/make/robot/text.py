from .chassis import Trait

MCR = 1_000_000


def format_traits(traits: list[Trait]) -> str:
    return ', '.join(str(t) for t in traits) if traits else '—'


def format_credits(amount: float) -> str:
    if amount >= MCR:
        return f'MCr{amount / MCR:g}'
    return f'Cr{int(amount):,}'


__all__ = ['format_credits', 'format_traits']
