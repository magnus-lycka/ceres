from ceres.character.careers.career_data import CharCheck
from ceres.character.characteristics import Chars
from ceres.character.precareers import load_precareers


def _entry(name: str) -> CharCheck:
    entry = load_precareers()[name].entry
    assert entry is not None
    return entry


def _graduation(name: str) -> CharCheck:
    graduation = load_precareers()[name].graduation
    assert graduation is not None
    return graduation


def test_core_precareers_are_loaded():
    precareers = load_precareers()

    assert {
        'Army Academy',
        'Colonial Upbringing',
        'Marine Academy',
        'Merchant Academy',
        'Navy Academy',
        'Psionic Community',
        'School of Hard Knocks',
        'Spacer Community',
        'University',
    } == set(precareers)


def test_all_precareers_are_four_years():
    assert {precareer.duration_years for precareer in load_precareers().values()} == {4}


def test_university_entry_and_graduation_rules_are_loaded():
    university = load_precareers()['University']

    assert _entry('University').characteristic == Chars.EDU
    assert _entry('University').target == 6
    assert _graduation('University').characteristic == Chars.INT
    assert _graduation('University').target == 6
    assert university.honours_target == 10
    assert university.skill_choices[0].skill == 'Admin'
    assert university.skill_choices[-1].skill == 'Science'


def test_military_academies_have_distinct_entry_and_same_graduation():
    precareers = load_precareers()

    assert _entry('Army Academy').characteristic == Chars.END
    assert _entry('Army Academy').target == 7
    assert _entry('Marine Academy').characteristic == Chars.END
    assert _entry('Marine Academy').target == 8
    assert _entry('Navy Academy').characteristic == Chars.INT
    assert _entry('Navy Academy').target == 8

    for name in ('Army Academy', 'Marine Academy', 'Navy Academy'):
        academy = precareers[name]
        assert _graduation(name).characteristic == Chars.INT
        assert _graduation(name).target == 7
        assert academy.honours_target == 11
        assert academy.tied_career is not None
        assert academy.service_skills_from == academy.tied_career


def test_precareer_events_are_loaded_once_for_all_precareers():
    university = load_precareers()['University']

    assert set(university.events) == set(range(2, 13))
    assert university.events[5].effects[0].type == 'gain_skill'
    assert university.events[7].effects[0].type == 'life_event'


def test_companion_precareers_are_loaded():
    precareers = load_precareers()

    assert precareers['Colonial Upbringing'].entry_requirement == 'Automatic if homeworld is TL8-'
    assert _graduation('Colonial Upbringing').target == 8
    assert precareers['Colonial Upbringing'].skill_choices[-1].skill == 'Survival'

    assert _entry('Merchant Academy').characteristic == Chars.INT
    assert _entry('Merchant Academy').target == 9
    assert precareers['Merchant Academy'].curricula == ['Business', 'Shipboard']

    assert precareers['Psionic Community'].entry_requirement == 'PSI 8+, DM+1 if INT 8+'
    assert precareers['Psionic Community'].graduation_requirement == 'PSI 6+, DM+1 if INT 8+'

    assert precareers['School of Hard Knocks'].entry_requirement == 'Automatic if SOC 6-'
    assert _graduation('School of Hard Knocks').target == 7

    assert (
        precareers['Spacer Community'].entry_requirement == 'Automatic if homeworld size code 0; INT 4+, DM+1 if DEX 8+'
    )
    assert _graduation('Spacer Community').target == 8
