from typing import Any

from pydantic import ValidationError
import pytest

from ceres.character.domain.skills import (
    Admin,
    CreativeArt,
    Electronics,
    LanguageVilani,
    Level,
    PhysicalScience,
    SpacerProfession,
    SpaceScience,
    Tactics,
    WorkerProfession,
)
from ceres.gear.software import (
    Agent,
    Expert,
    Intellect,
    IntelligentInterface,
    Interface,
    Security,
    Translator,
)


def test_interface_matches_csc_values():
    package = Interface()
    assert package.description == 'Interface'
    assert package.bandwidth == 0
    assert package.tl == 7
    assert package.cost == 0.0


def test_intelligent_interface_matches_csc_values():
    package = IntelligentInterface()
    assert package.description == 'Intelligent Interface'
    assert package.bandwidth == 1
    assert package.tl == 11
    assert package.cost == 100.0


def test_intellect_zero_represents_included_ship_intellect():
    package = Intellect(rating=0)
    assert package.description == 'Intellect'
    assert package.bandwidth == 0
    assert package.tl == 11
    assert package.cost == 0.0


def test_intellect_three_matches_csc_values():
    package = Intellect(rating=3)
    assert package.description == 'Intellect/3'
    assert package.bandwidth == 3
    assert package.tl == 14
    assert package.cost == 200_000.0


def test_expert_broad_science_planetology_matches_skill_table():
    package = Expert(rating=1, skill=SpaceScience(planetology=Level(value=1)))
    assert package.description == 'Expert (Space Science (Planetology))/1'
    assert package.bandwidth == 1
    assert package.tl == 9
    assert package.cost == 200.0


def test_expert_art_skill_uses_art_union_lookup():
    package = Expert(rating=1, skill=CreativeArt(visual_media=Level(value=1)))

    assert package.description == 'Expert (Creative Art (Visual Media))/1'
    assert package.bandwidth == 1
    assert package.tl == 9
    assert package.cost == 200.0


def test_expert_higher_rating_increases_tl_and_cost_from_base_skill():
    package = Expert(rating=3, skill=Admin(level=Level(value=3)))
    assert package.description == 'Expert (Admin)/3'
    assert package.bandwidth == 3
    assert package.tl == 10
    assert package.cost == 10_000.0


def test_expert_supports_all_companion_science_subskills():
    package = Expert(rating=2, skill=PhysicalScience(jumpspace_physics=Level(value=1)))
    assert package.description == 'Expert (Physical Science (Jumpspace Physics))/2'
    assert package.bandwidth == 2
    assert package.tl == 10
    assert package.cost == 2_000.0


def test_expert_known_specialised_skill_uses_skill_lookup_when_all_specialities_match():
    package = Expert(rating=1, skill=Electronics(computers=Level(value=1)))
    assert package.description == 'Expert (Electronics (Computers))/1'
    assert package.bandwidth == 1
    assert package.tl == 8
    assert package.cost == 100.0


def test_expert_known_broad_profession_subskill_uses_flat_lookup():
    package = Expert(rating=1, skill=SpacerProfession(crewmember=Level(value=1)))
    assert package.description == 'Expert (Spacer Profession (Crewmember))/1'
    assert package.bandwidth == 1
    assert package.tl == 9
    assert package.cost == 200.0


def test_expert_known_worker_profession_subskill_uses_flat_lookup():
    package = Expert(rating=1, skill=WorkerProfession(polymers=Level(value=1)))
    assert package.description == 'Expert (Worker Profession (Polymers))/1'
    assert package.bandwidth == 1
    assert package.tl == 9
    assert package.cost == 200.0


def test_expert_rejects_string_skill_input():
    bad_input: Any = 'Admin'
    with pytest.raises(ValidationError):
        Expert(rating=1, skill=bad_input)


def test_expert_known_skill_uses_skill_lookup_without_active_speciality_when_all_specialities_match():
    package = Expert(rating=1, skill=Tactics())
    assert package.description == 'Expert (Tactics)/1'
    assert package.bandwidth == 1
    assert package.tl == 8
    assert package.cost == 100.0
    assert not package.notes.warnings


def test_expert_language_vilani_uses_languages_union_lookup():
    package = Expert(rating=1, skill=LanguageVilani(level=Level(value=1)))
    assert package.description == 'Expert (Language Vilani)/1'
    assert package.tl == 9
    assert package.cost == 200.0
    assert package.bandwidth == 1


def test_expert_tactics_military_uses_known_lookup():
    package = Expert(rating=1, skill=Tactics(military=Level(value=1)))
    assert package.description == 'Expert (Tactics (Military))/1'
    assert package.tl == 8
    assert package.cost == 100.0
    assert package.bandwidth == 1


def test_expert_tactics_naval_uses_known_lookup():
    package = Expert(rating=1, skill=Tactics(naval=Level(value=1)))
    assert package.description == 'Expert (Tactics (Naval))/1'
    assert package.tl == 8
    assert package.cost == 100.0
    assert package.bandwidth == 1


def test_security_zero_matches_csc_values():
    package = Security(rating=0)
    assert package.description == 'Security/0'
    assert package.bandwidth == 0
    assert package.tl == 8
    assert package.cost == 0.0


def test_security_three_matches_csc_values():
    package = Security(rating=3)
    assert package.description == 'Security/3'
    assert package.bandwidth == 3
    assert package.tl == 12
    assert package.cost == 20_000.0


def test_security_rejects_invalid_rating():
    with pytest.raises(ValueError, match='Unsupported Security rating 4'):
        Security(rating=4)


def test_agent_zero_matches_csc_values():
    package = Agent(rating=0)
    assert package.description == 'Agent/0'
    assert package.bandwidth == 0
    assert package.tl == 11
    assert package.cost == 500.0


def test_agent_three_matches_csc_values():
    package = Agent(rating=3)
    assert package.description == 'Agent/3'
    assert package.bandwidth == 3
    assert package.tl == 14
    assert package.cost == 250_000.0


def test_translator_zero_matches_csc_values():
    package = Translator(rating=0)
    assert package.description == 'Translator/0'
    assert package.bandwidth == 0
    assert package.tl == 9
    assert package.cost == 50.0


def test_translator_one_matches_csc_values():
    package = Translator(rating=1)
    assert package.description == 'Translator/1'
    assert package.bandwidth == 1
    assert package.tl == 10
    assert package.cost == 500.0
