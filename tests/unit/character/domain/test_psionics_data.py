import pytest

from ceres.character.domain.psionics_data import (
    PSIONIC_TALENT_LEARNING_DMS,
    Awareness,
    Clairvoyance,
    Psionics,
    Telekinesis,
    Telepathy,
    Teleportation,
    psionic_talent_classes,
    psionic_talent_instances,
)
from ceres.character.domain.skills import Level


def test_psionic_talent_classes_match_learning_dm_table() -> None:
    assert psionic_talent_classes() == (
        Telepathy,
        Clairvoyance,
        Telekinesis,
        Awareness,
        Teleportation,
    )
    assert set(PSIONIC_TALENT_LEARNING_DMS) == set(psionic_talent_classes())


def test_psionic_talent_instances_are_default_level_talents() -> None:
    talents = psionic_talent_instances()

    assert [type(talent) for talent in talents] == list(psionic_talent_classes())
    assert all(talent.level.value == 0 for talent in talents)


@pytest.mark.parametrize('raw_roll', [1, 13])
def test_strength_test_rejects_out_of_range_rolls(raw_roll: int) -> None:
    with pytest.raises(ValueError, match='Psionic Strength roll must be 2-12'):
        Psionics.from_strength_test(raw_roll=raw_roll, terms_served=0)


def test_strength_test_returns_psi_and_psionics_state_when_positive() -> None:
    psi, psionics = Psionics.from_strength_test(raw_roll=9, terms_served=2)

    assert psi == 7
    assert psionics == Psionics()


def test_strength_test_returns_no_psionics_state_when_zero() -> None:
    psi, psionics = Psionics.from_strength_test(raw_roll=2, terms_served=5)

    assert psi == 0
    assert psionics is None


def test_talent_lookup_and_level_for_untrained_talent() -> None:
    psionics = Psionics(psionic_talent_skills=[Telepathy()])

    assert isinstance(psionics.talent(Telepathy), Telepathy)
    assert psionics.talent(Clairvoyance) is None
    assert psionics.talent_level(Telepathy) == 0
    assert psionics.talent_level(Clairvoyance) is None


def test_increment_talent_raises_for_untrained_talent() -> None:
    with pytest.raises(ValueError, match='Cannot improve untrained psionic talent Clairvoyance'):
        Psionics().increment_talent(Clairvoyance)


def test_increment_talent_caps_at_four() -> None:
    psionics = Psionics(psionic_talent_skills=[Telepathy(level=Level(value=4))])

    psionics.increment_talent(Telepathy)

    assert psionics.talent_level(Telepathy) == 4


def test_increment_talent_raises_level_below_cap() -> None:
    psionics = Psionics(psionic_talent_skills=[Telepathy(level=Level(value=2))])

    psionics.increment_talent(Telepathy)

    assert psionics.talent_level(Telepathy) == 3


def test_raise_talent_to_raises_for_invalid_level() -> None:
    with pytest.raises(ValueError, match='Psionic talent level must be 0-4'):
        Psionics(psionic_talent_skills=[Telepathy()]).raise_talent_to(Telepathy, 5)


def test_raise_talent_to_raises_for_untrained_talent() -> None:
    with pytest.raises(ValueError, match='Cannot improve untrained psionic talent Clairvoyance'):
        Psionics().raise_talent_to(Clairvoyance, 1)


def test_raise_talent_to_does_not_lower_existing_level() -> None:
    psionics = Psionics(psionic_talent_skills=[Telepathy(level=Level(value=3))])

    psionics.raise_talent_to(Telepathy, 1)

    assert psionics.talent_level(Telepathy) == 3


def test_attempt_talent_acquisition_rejects_duplicate_talent() -> None:
    psionics = Psionics(psionic_talent_skills=[Telepathy()])

    with pytest.raises(ValueError, match='Already trained in psionic talent Telepathy'):
        psionics.attempt_talent_acquisition(Telepathy, psi=9, raw_roll=8)


@pytest.mark.parametrize('raw_roll', [1, 13])
def test_attempt_talent_acquisition_rejects_out_of_range_roll(raw_roll: int) -> None:
    with pytest.raises(ValueError, match='Psionic talent acquisition roll must be 2-12'):
        Psionics().attempt_talent_acquisition(Clairvoyance, psi=9, raw_roll=raw_roll)


def test_first_telepathy_acquisition_is_automatic() -> None:
    psionics = Psionics()

    result = psionics.attempt_talent_acquisition(Telepathy, psi=3, raw_roll=2)

    assert result.success
    assert result.automatic
    assert result.total == 5
    assert psionics.talent_level(Telepathy) == 0
    assert psionics.talent_acquisition_checks == 1


def test_non_automatic_acquisition_uses_psi_dm_learning_dm_and_previous_checks() -> None:
    psionics = Psionics(talent_acquisition_checks=1)

    result = psionics.attempt_talent_acquisition(Clairvoyance, psi=9, raw_roll=6)

    assert result.success
    assert not result.automatic
    assert result.total == 9
    assert psionics.talent_level(Clairvoyance) == 0
    assert psionics.talent_acquisition_checks == 2


def test_failed_acquisition_counts_check_without_adding_talent() -> None:
    psionics = Psionics(talent_acquisition_checks=1)

    result = psionics.attempt_talent_acquisition(Telekinesis, psi=3, raw_roll=2)

    assert not result.success
    assert result.total == 2
    assert psionics.talent_level(Telekinesis) is None
    assert psionics.talent_acquisition_checks == 2
