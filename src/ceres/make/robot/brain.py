"""Robot brain types — Phase 1 stub.

Full table lookup (cost, bandwidth, base_int, skill_dm) is added in Phase 2
when refs/robot/33_brain.md is fully implemented.
"""

from typing import Annotated, Literal

from pydantic import Field

from ceres.shared import CeresModel


class _BrainBase(CeresModel):
    model_config = {'frozen': True}

    def programming_label(self) -> str:
        raise NotImplementedError


class PrimitiveBrain(_BrainBase):
    type: Literal['PRIMITIVE'] = 'PRIMITIVE'
    brain_tl: int = 8

    def programming_label(self) -> str:
        return 'Primitive'


class BasicBrain(_BrainBase):
    type: Literal['BASIC'] = 'BASIC'
    brain_tl: int = 10

    def programming_label(self) -> str:
        return 'Basic'


class AdvancedBrain(_BrainBase):
    type: Literal['ADVANCED'] = 'ADVANCED'
    brain_tl: int = 12

    def programming_label(self) -> str:
        # Phase 2 will look up INT from the brain table using brain_tl
        return 'Advanced (INT ?)'


RobotBrainUnion = Annotated[
    PrimitiveBrain | BasicBrain | AdvancedBrain,
    Field(discriminator='type'),
]

__all__ = [
    'RobotBrainUnion',
    'PrimitiveBrain',
    'BasicBrain',
    'AdvancedBrain',
]
