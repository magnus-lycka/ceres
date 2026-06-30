from typing import Annotated, Literal, cast, get_args, get_origin

from pydantic import BaseModel, Field, RootModel

from ceres.character.domain.characteristics import characteristic_dm
from ceres.character.domain.skills import Level, Skill, _level


class Telepathy(Skill):
    kind: Literal['TELEPATHY'] = 'TELEPATHY'
    level: Level = _level()


class Clairvoyance(Skill):
    kind: Literal['CLAIRVOYANCE'] = 'CLAIRVOYANCE'
    level: Level = _level()


class Telekinesis(Skill):
    kind: Literal['TELEKINESIS'] = 'TELEKINESIS'
    level: Level = _level()


class Awareness(Skill):
    kind: Literal['AWARENESS'] = 'AWARENESS'
    level: Level = _level()


class Teleportation(Skill):
    kind: Literal['TELEPORTATION'] = 'TELEPORTATION'
    level: Level = _level()


PsionicTalentSkillModels = Telepathy | Clairvoyance | Telekinesis | Awareness | Teleportation
type PsionicTalentSkills = Annotated[PsionicTalentSkillModels, Field(discriminator='kind')]
type PsionicTalentSkillClass = (
    type[Telepathy] | type[Clairvoyance] | type[Telekinesis] | type[Awareness] | type[Teleportation]
)


class Psi(RootModel[PsionicTalentSkills]):
    """A career-table entry resolved through psionic talent training."""

    @property
    def talent(self) -> PsionicTalentSkills:
        return self.root


PSIONIC_TALENT_LEARNING_DMS: dict[PsionicTalentSkillClass, int] = {
    Telepathy: 4,
    Clairvoyance: 3,
    Telekinesis: 2,
    Awareness: 1,
    Teleportation: 0,
}


def psionic_talent_classes() -> tuple[PsionicTalentSkillClass, ...]:
    union: object = PsionicTalentSkills
    if hasattr(union, '__value__'):
        union = union.__value__
    if get_origin(union) is Annotated:
        union = get_args(union)[0]
    return cast(tuple[PsionicTalentSkillClass, ...], get_args(union))


def psionic_talent_instances() -> list[PsionicTalentSkills]:
    return [cls() for cls in psionic_talent_classes()]


class TalentAcquisitionResult(BaseModel):
    talent: PsionicTalentSkills
    raw_roll: int
    total: int
    success: bool
    automatic: bool = False


class Psionics(BaseModel):
    psionic_talent_skills: list[PsionicTalentSkills] = Field(default_factory=list)
    talent_acquisition_checks: int = 0

    @classmethod
    def from_strength_test(cls, *, raw_roll: int, terms_served: int) -> tuple[int, Psionics | None]:
        if not 2 <= raw_roll <= 12:
            raise ValueError(f'Psionic Strength roll must be 2-12, got {raw_roll}')
        psi = max(0, raw_roll - terms_served)
        return psi, cls() if psi > 0 else None

    def talent(self, talent_cls: PsionicTalentSkillClass) -> PsionicTalentSkills | None:
        return next((talent for talent in self.psionic_talent_skills if type(talent) is talent_cls), None)

    def talent_level(self, talent_cls: PsionicTalentSkillClass) -> int | None:
        talent = self.talent(talent_cls)
        return talent.level.value if talent is not None else None

    def increment_talent(self, talent_cls: PsionicTalentSkillClass) -> None:
        talent = self.talent(talent_cls)
        if talent is None:
            raise ValueError(f'Cannot improve untrained psionic talent {talent_cls.name()}')
        if talent.level.value < 4:
            talent.level.value += 1

    def raise_talent_to(self, talent_cls: PsionicTalentSkillClass, level: int) -> None:
        if not 0 <= level <= 4:
            raise ValueError(f'Psionic talent level must be 0-4, got {level}')
        talent = self.talent(talent_cls)
        if talent is None:
            raise ValueError(f'Cannot improve untrained psionic talent {talent_cls.name()}')
        talent.level.value = max(talent.level.value, level)

    def attempt_talent_acquisition(
        self,
        talent_cls: PsionicTalentSkillClass,
        *,
        psi: int,
        raw_roll: int,
    ) -> TalentAcquisitionResult:
        if self.talent(talent_cls) is not None:
            raise ValueError(f'Already trained in psionic talent {talent_cls.name()}')
        if not 2 <= raw_roll <= 12:
            raise ValueError(f'Psionic talent acquisition roll must be 2-12, got {raw_roll}')

        previous_checks = self.talent_acquisition_checks
        automatic = talent_cls is Telepathy and previous_checks == 0
        total = raw_roll + characteristic_dm(psi) + PSIONIC_TALENT_LEARNING_DMS[talent_cls] - previous_checks
        success = automatic or total >= 8
        self.talent_acquisition_checks += 1
        talent = talent_cls()
        if success:
            self.psionic_talent_skills.append(talent)
        return TalentAcquisitionResult(
            talent=talent,
            raw_roll=raw_roll,
            total=total,
            success=success,
            automatic=automatic,
        )
