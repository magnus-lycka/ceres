"""Domain-level tests for draft table and draft alternative (RIC-003)."""

from ceres.character.domain.career import AGENT, ARMY, MARINES, MERCHANT, NAVY, SCOUT
from ceres.character.domain.career.citizen import CITIZEN
from ceres.character.domain.career.draft import build_draft_table, get_draft_alternative
from ceres.character.domain.career.drifter import DRIFTER
from ceres.character.domain.career.entertainer import ENTERTAINER
from ceres.character.domain.career.noble import NOBLE
from ceres.character.domain.career.rogue import ROGUE

# ── is_in_draft ───────────────────────────────────────────────────────────────


def test_is_in_draft_nonzero_for_standard_draft_careers():
    for career in (NAVY, ARMY, MARINES, MERCHANT, SCOUT, AGENT):
        assert career.is_in_draft(None) > 0


def test_is_in_draft_zero_for_non_draft_careers():
    for career in (CITIZEN, DRIFTER, ENTERTAINER, NOBLE, ROGUE):
        assert career.is_in_draft(None) == 0


# ── is_draft_alternative ─────────────────────────────────────────────────────


def test_is_draft_alternative_true_for_drifter():
    assert DRIFTER.is_draft_alternative(None) is True


def test_is_draft_alternative_false_for_draft_careers():
    for career in (NAVY, ARMY, MARINES, MERCHANT, SCOUT, AGENT):
        assert career.is_draft_alternative(None) is False


# ── build_draft_table ─────────────────────────────────────────────────────────


def test_build_draft_table_returns_the_six_standard_careers_in_alphabetical_order():
    careers = (NAVY, ARMY, MARINES, MERCHANT, SCOUT, AGENT, CITIZEN, DRIFTER)
    table = build_draft_table(summary=None, careers=careers)
    assert table == sorted([AGENT, ARMY, MARINES, MERCHANT, NAVY, SCOUT], key=lambda c: c.name)


def test_build_draft_table_excludes_non_draft_careers():
    careers = (NAVY, ARMY, CITIZEN, DRIFTER)
    table = build_draft_table(summary=None, careers=careers)
    assert CITIZEN not in table
    assert DRIFTER not in table


# ── get_draft_alternative ─────────────────────────────────────────────────────


def test_get_draft_alternative_returns_drifter():
    careers = (NAVY, ARMY, DRIFTER, CITIZEN)
    assert get_draft_alternative(summary=None, careers=careers) is DRIFTER


def test_get_draft_alternative_returns_none_when_no_alternative_exists():
    careers = (NAVY, ARMY, CITIZEN)
    assert get_draft_alternative(summary=None, careers=careers) is None
