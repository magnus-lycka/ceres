"""Which ShipPartMixin implementations are actually installable parts.

Some classes implement the mixin as a base for real parts rather than as a part
themselves. They are marked here explicitly, at the definition site, so that the
architecture conformance test can skip them without inferring intent from the
shape of the class tree.
"""

_NOT_INSTALLABLE: set[type] = set()


def not_installable[T: type](cls: T) -> T:
    """Mark a class as a base for parts rather than an installable part."""
    _NOT_INSTALLABLE.add(cls)
    return cls


def is_installable(cls: type) -> bool:
    return cls not in _NOT_INSTALLABLE
