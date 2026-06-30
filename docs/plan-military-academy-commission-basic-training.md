# Plan: Military Academy, Commission, and Basic Training Tracking

## Overview

This document outlines a Test-Driven Development (TDD) approach to fix the broken basic training tracking in the `ceres.character` module. The current implementation incorrectly repeats basic training in several scenarios that should be prevented.

## Problems to Address

### 1. RIC-009: Military Academy Graduates
Military Academy graduates already receive Service Skills at level 0 for the corresponding career. Therefore, basic training should **not be repeated** when entering that career after graduation.

### 2. Career Re-entry
If a Traveller follows a path like Scout → Drifter → Scout, basic training should **not be repeated** for the second Scout term.

### 3. RIC-010: Assignment Switch
For careers where assignments are treated as new careers (Agent, Citizen, Entertainer, Merchant), basic training should **still not be repeated** when switching assignments within the same career.

## Proposed Solution

### Core Idea
Add a **`basic_training: list[CareerData]`** field to `CharacterProjection` to track which careers have already granted basic training to the character.

### Implementation Details

#### 1. CharacterProjection Model Update
**File:** `src/ceres/character/domain/character_projection.py`

Add a new field to track basic training completion:
```python
basic_training: list[CareerData] = Field(default_factory=list)
```

#### 2. CareerData Basic Training Logic
**File:** `src/ceres/character/domain/career_data.py`

Update the `_basic_training_plan()` method:
- Check if the career is already in `projection.basic_training`
- If yes, return `None` (no basic training needed)
- If no, return `BasicTrainingPlan(grant_all=True)` for first career
- If no, return `BasicTrainingPlan(grant_all=False)` for subsequent careers

#### 3. Military Academy Handling
**File:** `src/ceres/character/domain/precareer/military_academy.py`

On graduation, add the tied career to `projection.basic_training`:
```python
projection.basic_training.append(tied_career)
```

#### 4. Assignment Switch Handling (RIC-010)
**Files:**
- `src/ceres/character/domain/career/agent.py`
- `src/ceres/character/domain/career/citizen.py`
- `src/ceres/character/domain/career/entertainer.py`
- `src/ceres/character/domain/career/merchant.py`

For assignment switches within the same career, check if the parent career is in `basic_training` before granting limited basic training.

## TDD Approach

### Step 1: Write Failing Tests

Create three test files to prove the current implementation is broken:

#### Test File 1: `tests/unit/character/test_basic_training_academy.py`
Tests that Military Academy graduates do **not** repeat basic training for the corresponding career.

#### Test File 2: `tests/unit/character/test_basic_training_reentry.py`
Tests that re-entering a career (e.g., Scout → Drifter → Scout) does **not** repeat basic training.

#### Test File 3: `tests/unit/character/test_basic_training_assignment_switch.py`
Tests that switching assignments within the same career (e.g., Citizen Worker → Citizen Corporate) does **not** repeat basic training.

### Step 2: Run Tests (They Should Fail)
```bash
uv run pytest tests/unit/character/test_basic_training_*.py -v
```

### Step 3: Implement the Fix
Update the code as described in the "Implementation Details" section above.

### Step 4: Run Tests Again (They Should Pass)
Re-run the tests to verify the fix:
```bash
uv run pytest tests/unit/character/test_basic_training_*.py -v
```

### Step 5: Add Edge Case Tests
Create additional tests for edge cases:
- Military Academy failure (roll 2 or less) → no basic training granted
- Military Academy failure (roll 3-6) → basic training granted, but no commission
- Multiple Military Academies (e.g., Army Academy → Navy Academy)
- Switching between careers with shared Service Skills

## Files to Modify

| File | Change |
|------|--------|
| `src/ceres/character/domain/character_projection.py` | Add `basic_training` field |
| `src/ceres/character/domain/career_data.py` | Update `_basic_training_plan()` |
| `src/ceres/character/domain/precareer/military_academy.py` | Add tied career to `basic_training` on graduation |
| `src/ceres/character/domain/career/agent.py` | Update assignment switch logic for RIC-010 |
| `src/ceres/character/domain/career/citizen.py` | Update assignment switch logic for RIC-010 |
| `src/ceres/character/domain/career/entertainer.py` | Update assignment switch logic for RIC-010 |
| `src/ceres/character/domain/career/merchant.py` | Update assignment switch logic for RIC-010 |

## Next Steps

1. **Review the plan** and provide feedback
2. **Implement the failing tests** first (TDD)
3. **Run the tests** to confirm they fail
4. **Implement the fix** as described
5. **Run the tests again** to confirm they pass
6. **Add edge case tests** for comprehensive coverage

## Verification Commands

```bash
# Run all basic training tests
uv run pytest tests/unit/character/test_basic_training_*.py -v

# Run with coverage
uv run pytest tests/unit/character/test_basic_training_*.py --cov=src/ceres/character --cov-report=term-missing -v

# Run the full test suite to ensure no regressions
uv run pytest tests/ -v
```

## Success Criteria

- All new tests pass
- No existing tests are broken
- The basic training tracking correctly prevents duplicate training in all three scenarios (RIC-009, career re-entry, RIC-010)
