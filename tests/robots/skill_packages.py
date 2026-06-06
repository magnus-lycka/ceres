from typing import cast

from ceres.character.domain import skills as character_skills
from ceres.character.domain.skills import Level, Skill
from ceres.make.robot.skills import RobotProfession, RobotSkill, SkillPackage


def _pkg(skill: Skill, level: int, bandwidth: int, *, all_specialities: bool = False) -> SkillPackage:
    return SkillPackage(
        name=cast(RobotSkill, skill),
        level=level,
        bandwidth=bandwidth,
        all_specialities=all_specialities,
    )


def admin(level: int, bandwidth: int) -> SkillPackage:
    return _pkg(character_skills.Admin(), level, bandwidth)


def advocate(level: int, bandwidth: int) -> SkillPackage:
    return _pkg(character_skills.Advocate(), level, bandwidth)


def animals_veterinary(level: int, bandwidth: int) -> SkillPackage:
    return _pkg(character_skills.Animals(veterinary=Level(value=1)), level, bandwidth)


def athletics_dexterity(level: int, bandwidth: int) -> SkillPackage:
    return _pkg(character_skills.Athletics(dexterity=Level(value=1)), level, bandwidth)


def athletics_strength(level: int, bandwidth: int) -> SkillPackage:
    return _pkg(character_skills.Athletics(strength=Level(value=1)), level, bandwidth)


def broker(level: int, bandwidth: int) -> SkillPackage:
    return _pkg(character_skills.Broker(), level, bandwidth)


def drive_all(level: int, bandwidth: int) -> SkillPackage:
    return _pkg(character_skills.Drive(), level, bandwidth, all_specialities=True)


def electronics_all(level: int, bandwidth: int) -> SkillPackage:
    return _pkg(character_skills.Electronics(), level, bandwidth, all_specialities=True)


def electronics_comms(level: int, bandwidth: int) -> SkillPackage:
    return _pkg(character_skills.Electronics(comms=Level(value=1)), level, bandwidth)


def electronics_remote_ops(level: int, bandwidth: int) -> SkillPackage:
    return _pkg(character_skills.Electronics(remote_ops=Level(value=1)), level, bandwidth)


def engineer_all(level: int, bandwidth: int) -> SkillPackage:
    return _pkg(character_skills.Engineer(), level, bandwidth, all_specialities=True)


def engineer_j_drive(level: int, bandwidth: int) -> SkillPackage:
    return _pkg(character_skills.Engineer(j_drive=Level(value=1)), level, bandwidth)


def explosives(level: int, bandwidth: int) -> SkillPackage:
    return _pkg(character_skills.Explosives(), level, bandwidth)


def flyer_all(level: int, bandwidth: int) -> SkillPackage:
    return _pkg(character_skills.Flyer(), level, bandwidth, all_specialities=True)


def flyer_grav(level: int, bandwidth: int) -> SkillPackage:
    return _pkg(character_skills.Flyer(grav=Level(value=1)), level, bandwidth)


def gun_combat(level: int, bandwidth: int) -> SkillPackage:
    return _pkg(character_skills.GunCombat(), level, bandwidth)


def investigate(level: int, bandwidth: int) -> SkillPackage:
    return _pkg(character_skills.Investigate(), level, bandwidth)


def language_vilani(level: int, bandwidth: int) -> SkillPackage:
    return _pkg(character_skills.LanguageVilani(), level, bandwidth)


def mechanic(level: int, bandwidth: int) -> SkillPackage:
    return _pkg(character_skills.Mechanic(), level, bandwidth)


def medic(level: int, bandwidth: int) -> SkillPackage:
    return _pkg(character_skills.Medic(), level, bandwidth)


def melee_unarmed(level: int, bandwidth: int) -> SkillPackage:
    return _pkg(character_skills.Melee(unarmed=Level(value=1)), level, bandwidth)


def navigation(level: int, bandwidth: int) -> SkillPackage:
    return _pkg(character_skills.Navigation(), level, bandwidth)


def pilot_small_craft(level: int, bandwidth: int) -> SkillPackage:
    return _pkg(character_skills.Pilot(small_craft=Level(value=1)), level, bandwidth)


def profession_belter(level: int, bandwidth: int) -> SkillPackage:
    return _pkg(character_skills.SpacerProfession(belter=Level(value=1)), level, bandwidth)


def profession_cleaning(level: int, bandwidth: int) -> SkillPackage:
    return _pkg(RobotProfession(cleaning=Level(value=1)), level, bandwidth)


def profession_fabricator(level: int, bandwidth: int) -> SkillPackage:
    return _pkg(RobotProfession(fabricator=Level(value=1)), level, bandwidth)


def profession_gardening(level: int, bandwidth: int) -> SkillPackage:
    return _pkg(RobotProfession(gardening=Level(value=1)), level, bandwidth)


def profession_robotics(level: int, bandwidth: int) -> SkillPackage:
    return _pkg(RobotProfession(robotics=Level(value=1)), level, bandwidth)


def recon(level: int, bandwidth: int) -> SkillPackage:
    return _pkg(character_skills.Recon(), level, bandwidth)


def science_biology(level: int, bandwidth: int) -> SkillPackage:
    return _pkg(character_skills.LifeScience(biology=Level(value=1)), level, bandwidth)


def science_chemistry(level: int, bandwidth: int) -> SkillPackage:
    return _pkg(character_skills.PhysicalScience(chemistry=Level(value=1)), level, bandwidth)


def science_robotics(level: int, bandwidth: int) -> SkillPackage:
    return _pkg(character_skills.RoboticScience(robotics=Level(value=1)), level, bandwidth)


def stealth(level: int, bandwidth: int) -> SkillPackage:
    return _pkg(character_skills.Stealth(), level, bandwidth)


def steward(level: int, bandwidth: int) -> SkillPackage:
    return _pkg(character_skills.Steward(), level, bandwidth)


def survival(level: int, bandwidth: int) -> SkillPackage:
    return _pkg(character_skills.Survival(), level, bandwidth)


def tactics_military(level: int, bandwidth: int) -> SkillPackage:
    return _pkg(character_skills.Tactics(military=Level(value=1)), level, bandwidth)
