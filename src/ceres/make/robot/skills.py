"""Installed skill packages and primitive brain skills for robots."""

from typing import ClassVar

from pydantic import ConfigDict

from ceres.character.domain.skills import (
    Skill,
    active_speciality_label,
)
from ceres.shared import CeresModel

from ._facades import *  # noqa: F403 — re-export all robot skill facades


def skill_name(skill: Skill) -> str:
    base = skill.name()
    speciality = active_speciality_label(skill)
    if speciality is None:
        return base
    return f'{base} ({speciality})'


_PRIMITIVE_SKILLS: dict[str, dict[str, int]] = {
    'alert': {'Recon': 0},
    'clean': {'Profession (Domestic Cleaner)': 2},
    'evade': {'Athletics (Dexterity)': 1, 'Stealth': 2},
    'homing': {'Weapon': 1},
    'labourer': {'Profession (Labourer)': 2},
    'locomotion': {'Athletics (Dexterity)': 1},
    'none': {},
    'recon': {'Recon': 2, 'Athletics (Dexterity)': 1},
    'servant': {'Profession (Domestic Servant)': 2},
}


def primitive_package_skills(function: str) -> dict[str, int]:
    return _PRIMITIVE_SKILLS.get(function, {})


class BrainSoftware(CeresModel):
    """Non-skill software installed in an Advanced (or higher) brain, consuming bandwidth.

    Used for software packages such as Universal Translator that run on the brain
    and consume bandwidth but do not grant skills.
    """

    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True)

    name: str
    bandwidth: int
    tl: int = 0
    cost: float = 0.0
