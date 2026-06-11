from ceres.character.domain import skills as character_skills
from ceres.character.domain.skills import Level
from ceres.make.robot.skills import RobotProfession, SkillPackage


def _level(n: int) -> Level:
    return Level(value=n)


def _pkg_simple(skill_cls, level: int) -> SkillPackage:
    """Unspecialised skill package (skill has a 'level' field)."""
    return SkillPackage(skill=skill_cls(level=_level(level)))


def _pkg_spec(skill_cls, field: str, level: int) -> SkillPackage:
    """Specific speciality skill package.

    At level 0, the speciality field is set to 1 to activate it, with
    package_level=0 to keep bandwidth and cost at the level-0 rate.
    """
    value = max(level, 1) if level == 0 else level
    pkg_level = 0 if level == 0 else None
    return SkillPackage(skill=skill_cls(**{field: _level(value)}), package_level=pkg_level)


def _pkg_all(skill_cls, level: int) -> SkillPackage:
    """All-specialities package. At level 0 no package_level override is needed."""
    if level == 0:
        return SkillPackage(skill=skill_cls())
    return SkillPackage(skill=skill_cls(), package_level=level)


def admin(level: int, bandwidth: int) -> SkillPackage:
    return _pkg_simple(character_skills.Admin, level)


def advocate(level: int, bandwidth: int) -> SkillPackage:
    return _pkg_simple(character_skills.Advocate, level)


def animals_veterinary(level: int, bandwidth: int) -> SkillPackage:
    return _pkg_spec(character_skills.Animals, 'veterinary', level)


def athletics_dexterity(level: int, bandwidth: int) -> SkillPackage:
    return _pkg_spec(character_skills.Athletics, 'dexterity', level)


def athletics_strength(level: int, bandwidth: int) -> SkillPackage:
    return _pkg_spec(character_skills.Athletics, 'strength', level)


def broker(level: int, bandwidth: int) -> SkillPackage:
    return _pkg_simple(character_skills.Broker, level)


def drive_all(level: int, bandwidth: int) -> SkillPackage:
    return _pkg_all(character_skills.Drive, level)


def electronics_all(level: int, bandwidth: int) -> SkillPackage:
    return _pkg_all(character_skills.Electronics, level)


def electronics_comms(level: int, bandwidth: int) -> SkillPackage:
    if level == 0:
        return _pkg_all(character_skills.Electronics, 0)
    return _pkg_spec(character_skills.Electronics, 'comms', level)


def electronics_remote_ops(level: int, bandwidth: int) -> SkillPackage:
    if level == 0:
        return _pkg_all(character_skills.Electronics, 0)
    return _pkg_spec(character_skills.Electronics, 'remote_ops', level)


def engineer_all(level: int, bandwidth: int) -> SkillPackage:
    return _pkg_all(character_skills.Engineer, level)


def engineer_j_drive(level: int, bandwidth: int) -> SkillPackage:
    if level == 0:
        return _pkg_all(character_skills.Engineer, 0)
    return _pkg_spec(character_skills.Engineer, 'j_drive', level)


def explosives(level: int, bandwidth: int) -> SkillPackage:
    return _pkg_simple(character_skills.Explosives, level)


def flyer_all(level: int, bandwidth: int) -> SkillPackage:
    return _pkg_all(character_skills.Flyer, level)


def flyer_grav(level: int, bandwidth: int) -> SkillPackage:
    if level == 0:
        return _pkg_all(character_skills.Flyer, 0)
    return _pkg_spec(character_skills.Flyer, 'grav', level)


def gun_combat(level: int, bandwidth: int) -> SkillPackage:
    pkg_level = level if level > 0 else None
    return SkillPackage(skill=character_skills.GunCombat(), package_level=pkg_level, expand_specialities=False)


def investigate(level: int, bandwidth: int) -> SkillPackage:
    return _pkg_simple(character_skills.Investigate, level)


def language_vilani(level: int, bandwidth: int) -> SkillPackage:
    return _pkg_spec(character_skills.LanguageVilani, 'vilani', level)


def mechanic(level: int, bandwidth: int) -> SkillPackage:
    return _pkg_simple(character_skills.Mechanic, level)


def medic(level: int, bandwidth: int) -> SkillPackage:
    return _pkg_simple(character_skills.Medic, level)


def melee_unarmed(level: int, bandwidth: int) -> SkillPackage:
    if level == 0:
        return _pkg_all(character_skills.Melee, 0)
    return _pkg_spec(character_skills.Melee, 'unarmed', level)


def navigation(level: int, bandwidth: int) -> SkillPackage:
    return _pkg_simple(character_skills.Navigation, level)


def pilot_small_craft(level: int, bandwidth: int) -> SkillPackage:
    return _pkg_spec(character_skills.Pilot, 'small_craft', level)


def profession_belter(level: int, bandwidth: int) -> SkillPackage:
    return _pkg_spec(character_skills.SpacerProfession, 'belter', level)


def profession_cleaning(level: int, bandwidth: int) -> SkillPackage:
    return _pkg_spec(RobotProfession, 'cleaning', level)


def profession_fabricator(level: int, bandwidth: int) -> SkillPackage:
    return _pkg_spec(RobotProfession, 'fabricator', level)


def profession_gardening(level: int, bandwidth: int) -> SkillPackage:
    return _pkg_spec(RobotProfession, 'gardening', level)


def profession_robotics(level: int, bandwidth: int) -> SkillPackage:
    return _pkg_spec(RobotProfession, 'robotics', level)


def recon(level: int, bandwidth: int) -> SkillPackage:
    return _pkg_simple(character_skills.Recon, level)


def science_biology(level: int, bandwidth: int) -> SkillPackage:
    return _pkg_spec(character_skills.LifeScience, 'biology', level)


def science_chemistry(level: int, bandwidth: int) -> SkillPackage:
    return _pkg_spec(character_skills.PhysicalScience, 'chemistry', level)


def science_robotics(level: int, bandwidth: int) -> SkillPackage:
    return _pkg_spec(character_skills.RoboticScience, 'robotics', level)


def stealth(level: int, bandwidth: int) -> SkillPackage:
    return _pkg_simple(character_skills.Stealth, level)


def steward(level: int, bandwidth: int) -> SkillPackage:
    return _pkg_simple(character_skills.Steward, level)


def survival(level: int, bandwidth: int) -> SkillPackage:
    return _pkg_simple(character_skills.Survival, level)


def tactics_military(level: int, bandwidth: int) -> SkillPackage:
    if level == 0:
        return _pkg_all(character_skills.Tactics, 0)
    return _pkg_spec(character_skills.Tactics, 'military', level)
