from enum import StrEnum


class EffectTrigger(StrEnum):
    ADVANCEMENT = 'advancement'
    MUSTER_OUT = 'muster_out'
    QUALIFICATION = 'qualification'
    AUTO_QUALIFY = 'auto_qualify'


class EffectType(StrEnum):
    DM = 'dm'
