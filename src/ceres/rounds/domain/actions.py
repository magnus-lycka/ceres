"""The small set of combat events the tracker records."""

from enum import StrEnum


class AttackKind(StrEnum):
    """The only actor actions recorded by the tracker."""

    MELEE = 'Melee'
    RANGED = 'Ranged'


class ReactionKind(StrEnum):
    """Reactions whose consequences the tracker needs to remember."""

    DODGE = 'Dodge'
    PARRY = 'Parry'
    DIVE = 'Dive'
