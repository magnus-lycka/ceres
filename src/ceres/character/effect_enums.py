from enum import StrEnum


class EffectTrigger(StrEnum):
    ADVANCEMENT = 'advancement'
    MUSTER_OUT = 'muster_out'
    MUSTER_OUT_ADD = 'muster_out_add'
    MUSTER_OUT_REDUCE = 'muster_out_reduce'
    QUALIFICATION = 'qualification'
    AUTO_QUALIFY = 'auto_qualify'


class EffectType(StrEnum):
    DM = 'dm'
    ADD = 'add'
    REDUCE = 'reduce'
