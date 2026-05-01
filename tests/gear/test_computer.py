import pytest

from ceres.gear.computer import Expert, Intellect, IntelligentInterface, Interface


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
    package = Intellect(0)
    assert package.description == 'Intellect/0'
    assert package.bandwidth == 0
    assert package.tl == 11
    assert package.cost == 0.0


def test_intellect_three_matches_csc_values():
    package = Intellect(3)
    assert package.description == 'Intellect/3'
    assert package.bandwidth == 3
    assert package.tl == 14
    assert package.cost == 200_000.0


def test_expert_broad_science_planetology_matches_skill_table():
    package = Expert(1, skill='Space Sciences (Planetology)')
    assert package.description == 'Expert (Space Sciences (Planetology))/1'
    assert package.bandwidth == 1
    assert package.tl == 9
    assert package.cost == 200.0


def test_expert_higher_rating_increases_tl_and_cost_from_base_skill():
    package = Expert(3, skill='Admin')
    assert package.description == 'Expert (Admin)/3'
    assert package.bandwidth == 3
    assert package.tl == 10
    assert package.cost == 10_000.0


def test_expert_supports_all_companion_science_subskills():
    package = Expert(2, skill='Physical Sciences (Jumpspace Physics)')
    assert package.description == 'Expert (Physical Sciences (Jumpspace Physics))/2'
    assert package.bandwidth == 2
    assert package.tl == 10
    assert package.cost == 2_000.0


def test_expert_rejects_plain_science_in_broad_skills_mode():
    with pytest.raises(ValueError, match='Science is a broad skill'):
        Expert(1, skill='Science')


def test_expert_rejects_plain_profession_in_broad_skills_mode():
    with pytest.raises(ValueError, match='Profession is a broad skill'):
        Expert(1, skill='Profession')


def test_expert_rejects_plain_art_in_broad_skills_mode():
    with pytest.raises(ValueError, match='Art is a broad skill'):
        Expert(1, skill='Art')


def test_expert_known_specialised_skill_uses_flat_lookup():
    package = Expert(1, skill='Electronics (Computers)')
    assert package.description == 'Expert (Electronics (Computers))/1'
    assert package.bandwidth == 1
    assert package.tl == 8
    assert package.cost == 100.0


def test_expert_known_broad_profession_subskill_uses_flat_lookup():
    package = Expert(1, skill='Spacer Profession (Crewmember)')
    assert package.description == 'Expert (Spacer Profession (Crewmember))/1'
    assert package.bandwidth == 1
    assert package.tl == 9
    assert package.cost == 200.0


def test_expert_known_worker_profession_subskill_uses_flat_lookup():
    package = Expert(1, skill='Worker Profession (Polymers)')
    assert package.description == 'Expert (Worker Profession (Polymers))/1'
    assert package.bandwidth == 1
    assert package.tl == 9
    assert package.cost == 200.0


def test_expert_unknown_skill_uses_csc_fallback_and_warns():
    package = Expert(1, skill='Cementology')
    assert package.description == 'Expert (Cementology)/1'
    assert package.bandwidth == 1
    assert package.tl == 11
    assert package.cost == 1_000.0
    assert ('warning', 'Unfamiliar Expert skill Cementology uses CSC fallback values') in [
        (note.category.value, note.message) for note in package.notes
    ]


def test_expert_tactics_any_falls_back_like_unknown_skill():
    cementology = Expert(1, skill='Cementology')
    tactics_any = Expert(1, skill='Tactics (Any)')
    assert tactics_any.description == 'Expert (Tactics (Any))/1'
    assert tactics_any.bandwidth == cementology.bandwidth
    assert tactics_any.tl == cementology.tl
    assert tactics_any.cost == cementology.cost
    assert ('warning', 'Unfamiliar Expert skill Tactics (Any) uses CSC fallback values') in [
        (note.category.value, note.message) for note in tactics_any.notes
    ]
