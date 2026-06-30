"""Approval snapshots for companion precareer flows (entry, graduation, honours)."""

import pytest

from ceres.character.domain.precareer.colonial_upbringing import ColonialUprbringingPreCareer
from ceres.character.domain.precareer.merchant_academy import (
    MerchantAcademyBusinessPreCareer,
    MerchantAcademyShipboardPreCareer,
)
from ceres.character.domain.precareer.psionic_community import PsionicCommunityPreCareer
from ceres.character.domain.precareer.school_of_hard_knocks import SchoolOfHardKnocksPreCareer
from ceres.character.domain.precareer.spacer_community import SpacerCommunityPreCareer
from ceres.character.domain.precareer.university import UniversityPreCareer
from ceres.character.domain.skills import Admin, Broker, Carouse, ColonistProfession, Level, LifeScience, Stealth
from ceres.character.domain.sophont import HUMANITI
from tests.approval.character.helpers import (
    MOCK_PSI_WORLD,
    CharacterSession,
    background_skills_form,
    precareer_entry_form,
    roll_form,
    skill_form,
    ucp_form,
)
from tests.approval.character.uc.conftest import projection_snap as _snap
from tests.approval.snapshot import AnnotatedJSONSnapshotExtension
from tests.unit.character.helpers import MOCK_WORLD

_ext = AnnotatedJSONSnapshotExtension


def _base_session() -> CharacterSession:
    """UCP 777727: STR=7 DEX=7 END=7 INT=7 EDU=2 SOC=7. EDU=2 → DM=-2 → 1 background skill."""
    session = CharacterSession()
    session.start(HUMANITI, MOCK_WORLD)
    session.submit(ucp_form('777727'))
    session.submit(background_skills_form(Admin()))
    return session


def _psi_base_session() -> CharacterSession:
    """Non-aligned world: after background skills PSI test is offered. Accept and roll 9 → PSI=9."""
    session = CharacterSession()
    session.start(HUMANITI, MOCK_PSI_WORLD)
    session.submit(ucp_form('777727'))
    session.submit(background_skills_form(Admin()))
    session.submit({'test': 'yes'})  # PendingInitialPsiTest → accept
    session.submit(roll_form(9))  # PendingInitialPsiStrengthRoll → PSI=9
    return session


def _psi_precareer_session(pc_roll: int) -> CharacterSession:
    """Drive through Psionic Community entry. Finishes institute training without training any talent.

    Psionic Community entry queues PendingPsionicInstituteTraining (at position 0) before the
    2 skill picks. Submitting {'talent': 'finish'} skips talent training so the 2 skill picks
    become the next pendingsinputs.
    """
    session = _psi_base_session()
    session.submit(precareer_entry_form(PsionicCommunityPreCareer, roll=pc_roll))
    if pc_roll > 1:
        session.submit({'talent': 'finish'})  # PendingPsionicInstituteTraining → no talent acquired
    return session


# ── Colonial Upbringing ───────────────────────────────────────────────────────


@pytest.mark.approval
def test_colonial_entry(snapshot):
    """Entry auto-grants 9 level-0 skills + Survival-1, queues 1 profession pick + event + graduation."""
    session = _base_session()
    session.submit(precareer_entry_form(ColonialUprbringingPreCareer, roll=5))
    assert _snap(session.projection) == snapshot(extension_class=_ext)


@pytest.mark.approval
def test_colonial_graduation(snapshot):
    """Graduation grants Jack-of-All-Trades-1, END+1, queues 3 level-1 picks and career choice."""
    session = _base_session()
    session.submit(precareer_entry_form(ColonialUprbringingPreCareer, roll=5))
    session.submit(skill_form(ColonistProfession()))
    session.submit(roll_form(5))  # precareer event
    session.submit(roll_form(10))  # graduation
    assert _snap(session.projection) == snapshot(extension_class=_ext)


@pytest.mark.approval
def test_colonial_failed_graduation(snapshot):
    """Failed graduation (roll too low) does not grant Jack-of-All-Trades or END+1."""
    session = _base_session()
    session.submit(precareer_entry_form(ColonialUprbringingPreCareer, roll=5))
    session.submit(skill_form(ColonistProfession()))
    session.submit(roll_form(5))  # precareer event
    session.submit(roll_form(1))  # graduation fails
    assert _snap(session.projection) == snapshot(extension_class=_ext)


@pytest.mark.approval
def test_colonial_honours_graduation(snapshot):
    """Honours graduation (roll >= 12) also grants Leadership and an extra pick."""
    session = _base_session()
    session.submit(precareer_entry_form(ColonialUprbringingPreCareer, roll=5))
    session.submit(skill_form(ColonistProfession()))
    session.submit(roll_form(5))  # precareer event
    session.submit(roll_form(12))  # graduation with honours
    assert _snap(session.projection) == snapshot(extension_class=_ext)


# ── Merchant Academy ──────────────────────────────────────────────────────────


@pytest.mark.approval
def test_merchant_business_entry(snapshot):
    """Business entry grants Broker table skills at level 0 and queues 1 service-skill pick."""
    session = _base_session()
    session.submit(precareer_entry_form(MerchantAcademyBusinessPreCareer, roll=9))
    assert _snap(session.projection) == snapshot(extension_class=_ext)


@pytest.mark.approval
def test_merchant_business_graduation(snapshot):
    """Business graduation increments EDU+1 and queues 1 curriculum pick."""
    session = _base_session()
    session.submit(precareer_entry_form(MerchantAcademyBusinessPreCareer, roll=9))
    session.submit(skill_form(Broker()))
    session.submit(roll_form(5))  # precareer event
    session.submit(roll_form(9))  # graduation
    assert _snap(session.projection) == snapshot(extension_class=_ext)


@pytest.mark.approval
def test_merchant_business_honours(snapshot):
    """Honours graduation (roll >= 11) gives advancement_dm+2 and rank-2 entry."""
    session = _base_session()
    session.submit(precareer_entry_form(MerchantAcademyBusinessPreCareer, roll=9))
    session.submit(skill_form(Broker()))
    session.submit(roll_form(5))  # precareer event
    session.submit(roll_form(12))  # graduation with honours
    assert _snap(session.projection) == snapshot(extension_class=_ext)


@pytest.mark.approval
def test_merchant_shipboard_entry(snapshot):
    """Shipboard entry grants Merchant Marine table skills (not Broker) at level 0."""
    session = _base_session()
    session.submit(precareer_entry_form(MerchantAcademyShipboardPreCareer, roll=9))
    assert _snap(session.projection) == snapshot(extension_class=_ext)


# ── Psionic Community ─────────────────────────────────────────────────────────


@pytest.mark.approval
def test_psionic_failed_entry(snapshot):
    """Failed psionic entry (roll too low) returns to career choice immediately."""
    session = _psi_precareer_session(pc_roll=1)
    assert _snap(session.projection) == snapshot(extension_class=_ext)


@pytest.mark.approval
def test_psionic_entry(snapshot):
    """Successful entry: Streetwise auto-granted, PsionicInstituteTraining queued first, then 2 skill picks."""
    session = _psi_base_session()
    session.submit(precareer_entry_form(PsionicCommunityPreCareer, roll=12))
    assert _snap(session.projection) == snapshot(extension_class=_ext)


@pytest.mark.approval
def test_psionic_graduation(snapshot):
    """Graduation (no talents acquired): grants Psionicology-1, PSI+1, auto-qualifies Psion, rival."""
    session = _psi_precareer_session(pc_roll=12)
    session.submit(skill_form(LifeScience(biology=Level(value=0))))
    session.submit(skill_form(LifeScience(biology=Level(value=0))))
    session.submit(roll_form(5))  # precareer event
    session.submit(roll_form(9))  # graduation (PSI 6+; PSI=9 DM+1 → 10 ≥ 6)
    assert _snap(session.projection) == snapshot(extension_class=_ext)


@pytest.mark.approval
def test_psionic_honours_graduation(snapshot):
    """Honours graduation (roll >= 12, no talents acquired): Psionicology-1, PSI+1, enemy connection."""
    session = _psi_precareer_session(pc_roll=12)
    session.submit(skill_form(LifeScience(biology=Level(value=0))))
    session.submit(skill_form(LifeScience(biology=Level(value=0))))
    session.submit(roll_form(5))  # precareer event
    session.submit(roll_form(12))  # graduation with honours
    assert _snap(session.projection) == snapshot(extension_class=_ext)


@pytest.mark.approval
def test_psionic_failed_graduation(snapshot):
    """Failed graduation (natural 2) does not grant Psionicology or PSI+1."""
    session = _psi_precareer_session(pc_roll=12)
    session.submit(skill_form(LifeScience(biology=Level(value=0))))
    session.submit(skill_form(LifeScience(biology=Level(value=0))))
    session.submit(roll_form(5))  # precareer event
    session.submit(roll_form(2))  # graduation fails (natural 2 is always a mishap/fail)
    assert _snap(session.projection) == snapshot(extension_class=_ext)


# ── School of Hard Knocks ─────────────────────────────────────────────────────


@pytest.mark.approval
def test_hard_knocks_entry(snapshot):
    """Entry grants Streetwise-1 and queues 2 level-0 picks."""
    session = _base_session()
    session.submit(precareer_entry_form(SchoolOfHardKnocksPreCareer, roll=5))
    assert _snap(session.projection) == snapshot(extension_class=_ext)


@pytest.mark.approval
def test_hard_knocks_graduation(snapshot):
    """Graduation grants Gun Combat-0, decreases SOC by 1, queues 3 level-0 picks."""
    session = _base_session()
    session.submit(precareer_entry_form(SchoolOfHardKnocksPreCareer, roll=5))
    session.submit(skill_form(Carouse()))
    session.submit(skill_form(Carouse()))
    session.submit(roll_form(5))  # precareer event
    session.submit(roll_form(8))  # graduation
    assert _snap(session.projection) == snapshot(extension_class=_ext)


@pytest.mark.approval
def test_hard_knocks_honours_graduation(snapshot):
    """Honours graduation (roll >= 11) additionally grants Carouse-1 and an extra pick."""
    session = _base_session()
    session.submit(precareer_entry_form(SchoolOfHardKnocksPreCareer, roll=5))
    session.submit(skill_form(Carouse()))
    session.submit(skill_form(Carouse()))
    session.submit(roll_form(5))  # precareer event
    session.submit(roll_form(12))  # graduation with honours
    assert _snap(session.projection) == snapshot(extension_class=_ext)


# ── Spacer Community ──────────────────────────────────────────────────────────


@pytest.mark.approval
def test_spacer_entry(snapshot):
    """Entry grants Vacc Suit-1 and queues 2 level-0 picks."""
    session = _base_session()
    session.submit(precareer_entry_form(SpacerCommunityPreCareer, roll=5))
    assert _snap(session.projection) == snapshot(extension_class=_ext)


@pytest.mark.approval
def test_spacer_graduation(snapshot):
    """Graduation grants Pilot-0, DEX+1, SOC-2, and queues 3 picks + career choice."""
    session = _base_session()
    session.submit(precareer_entry_form(SpacerCommunityPreCareer, roll=5))
    session.submit(skill_form(Stealth()))
    session.submit(skill_form(Stealth()))
    session.submit(roll_form(5))  # precareer event
    session.submit(roll_form(9))  # graduation
    assert _snap(session.projection) == snapshot(extension_class=_ext)


@pytest.mark.approval
def test_spacer_honours_graduation(snapshot):
    """Honours graduation (roll >= 12) additionally grants Jack-of-All-Trades."""
    session = _base_session()
    session.submit(precareer_entry_form(SpacerCommunityPreCareer, roll=5))
    session.submit(skill_form(Stealth()))
    session.submit(skill_form(Stealth()))
    session.submit(roll_form(5))  # precareer event
    session.submit(roll_form(12))  # graduation with honours
    assert _snap(session.projection) == snapshot(extension_class=_ext)


# ── University ────────────────────────────────────────────────────────────────


@pytest.mark.approval
def test_university_entry(snapshot):
    """Entry queues a level-0 and a level-1 skill pick."""
    session = _base_session()
    session.submit(precareer_entry_form(UniversityPreCareer, roll=10))
    assert _snap(session.projection) == snapshot(extension_class=_ext)


@pytest.mark.approval
def test_university_graduation(snapshot):
    """Graduation increments the chosen skills and queues career choice."""
    session = _base_session()
    session.submit(precareer_entry_form(UniversityPreCareer, roll=10))
    session.submit(skill_form(Admin()))
    session.submit(skill_form(Admin()))
    session.submit(roll_form(7))  # precareer event
    session.submit(roll_form(8))  # graduation
    assert _snap(session.projection) == snapshot(extension_class=_ext)


@pytest.mark.approval
def test_university_honours_graduation(snapshot):
    """University honours graduation (roll >= 10) queues career choice too."""
    session = _base_session()
    session.submit(precareer_entry_form(UniversityPreCareer, roll=10))
    session.submit(skill_form(Admin()))
    session.submit(skill_form(Admin()))
    session.submit(roll_form(7))  # precareer event
    session.submit(roll_form(11))  # graduation with honours
    assert _snap(session.projection) == snapshot(extension_class=_ext)
