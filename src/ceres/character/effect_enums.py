from enum import StrEnum


class EffectTrigger(StrEnum):
    ADVANCEMENT = 'advancement'
    QUALIFICATION = 'qualification'
    AUTO_QUALIFY = 'auto_qualify'


class EffectType(StrEnum):
    DM = 'dm'
