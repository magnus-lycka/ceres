"""Unit tests for muster-out benefit types and constants."""

from ceres.character.domain.benefits import (
    ALLY,
    ARMOR,
    BLADE,
    COMBAT_IMPLANT,
    CONTACT,
    CYBERNETIC_IMPLANT,
    DECEPTION_ITEM,
    FAR_TRADER,
    FREE_TRADER,
    GUN,
    LAB_SHIP,
    MELEE_ITEM,
    PERSONAL_VEHICLE,
    PERSUADE_ITEM,
    RECON_ITEM,
    SAFARI_SHIP,
    SCIENTIFIC_EQUIPMENT,
    SCOUT_SHIP,
    SHIP_SHARE,
    SHIPS_BOAT,
    STEALTH_ITEM,
    STREETWISE_ITEM,
    SUBSIDISED_MERCHANT,
    TAS_MEMBERSHIP,
    WEAPON,
    YACHT,
    CharacteristicIncrease,
    CombinedBenefit,
    ItemBenefit,
)
from ceres.character.domain.career import SCOUT
from ceres.character.domain.career.career_data import CareerTerm
from ceres.character.domain.character_state import CharacterProjection, CharacterSummary
from ceres.character.domain.characteristics import Chars
from ceres.character.domain.sophont import VILANI
from tests.character.helpers import MOCK_WORLD


def _projection_with_term(characteristics: dict[Chars, int] | None = None) -> CharacterProjection:
    courier = SCOUT.assignment('Courier')
    assert courier is not None
    return CharacterProjection(
        character_id=1,
        summary=CharacterSummary(
            name='Test',
            sophont=VILANI,
            homeworld=MOCK_WORLD,
            characteristics=characteristics or {},
            career_terms=[CareerTerm(career=SCOUT, assignment=courier)],
        ),
    )


class TestItemBenefitConstants:
    def test_ship_share_attributes(self):
        assert SHIP_SHARE.key == 'ship_share'
        assert SHIP_SHARE.label == 'Ship Share'
        assert not SHIP_SHARE.exceptional

    def test_scout_ship_is_exceptional(self):
        assert SCOUT_SHIP.key == 'scout_ship'
        assert SCOUT_SHIP.exceptional

    def test_yacht_is_exceptional(self):
        assert YACHT.key == 'yacht'
        assert YACHT.exceptional

    def test_weapon_not_exceptional(self):
        assert WEAPON.key == 'weapon'
        assert not WEAPON.exceptional

    def test_blade_not_exceptional(self):
        assert BLADE.key == 'blade'
        assert BLADE.label == 'Blade'
        assert not BLADE.exceptional

    def test_ships_boat_label(self):
        assert SHIPS_BOAT.key == 'ships_boat'
        assert SHIPS_BOAT.label == "Ship's Boat"

    def test_contact_label(self):
        assert CONTACT.key == 'contact'
        assert CONTACT.label == 'Contact'

    def test_ally_label(self):
        assert ALLY.key == 'ally'
        assert ALLY.label == 'Ally'

    def test_all_constants_are_item_benefits(self):
        for constant in (
            ALLY,
            ARMOR,
            BLADE,
            COMBAT_IMPLANT,
            CONTACT,
            CYBERNETIC_IMPLANT,
            DECEPTION_ITEM,
            FAR_TRADER,
            FREE_TRADER,
            GUN,
            LAB_SHIP,
            MELEE_ITEM,
            PERSONAL_VEHICLE,
            PERSUADE_ITEM,
            RECON_ITEM,
            SAFARI_SHIP,
            SCIENTIFIC_EQUIPMENT,
            SCOUT_SHIP,
            SHIP_SHARE,
            SHIPS_BOAT,
            STEALTH_ITEM,
            STREETWISE_ITEM,
            SUBSIDISED_MERCHANT,
            TAS_MEMBERSHIP,
            WEAPON,
            YACHT,
        ):
            assert isinstance(constant, ItemBenefit)


class TestCombinedBenefit:
    def test_display_label_joins_with_and(self):
        combined = CombinedBenefit(
            benefits=[
                CharacteristicIncrease(char=Chars.SOC, amount=1),
                YACHT,
            ]
        )
        assert combined.display_label == 'SOC +1 and Yacht'

    def test_display_label_three_items(self):
        combined = CombinedBenefit(benefits=[DECEPTION_ITEM, PERSUADE_ITEM, STEALTH_ITEM])
        assert combined.display_label == 'Deception and Persuade and Stealth'

    def test_exceptional_when_any_item_exceptional(self):
        combined = CombinedBenefit(
            benefits=[
                CharacteristicIncrease(char=Chars.SOC, amount=1),
                YACHT,
            ]
        )
        assert combined.exceptional

    def test_not_exceptional_when_none_exceptional(self):
        combined = CombinedBenefit(
            benefits=[
                CharacteristicIncrease(char=Chars.SOC, amount=1),
                CharacteristicIncrease(char=Chars.EDU, amount=1),
            ]
        )
        assert not combined.exceptional

    def test_type_discriminator(self):
        combined = CombinedBenefit(benefits=[SHIP_SHARE])
        assert isinstance(combined, CombinedBenefit)

    def test_apply_increments_all_characteristics(self):
        projection = _projection_with_term({Chars.SOC: 5, Chars.EDU: 10})
        combined = CombinedBenefit(
            benefits=[
                CharacteristicIncrease(char=Chars.SOC, amount=1),
                CharacteristicIncrease(char=Chars.EDU, amount=1),
            ]
        )
        combined.apply(projection)
        assert projection.summary.characteristics[Chars.SOC] == 6
        assert projection.summary.characteristics[Chars.EDU] == 11

    def test_apply_appends_all_item_benefits(self):
        projection = _projection_with_term()
        combined = CombinedBenefit(benefits=[SHIP_SHARE, WEAPON])
        combined.apply(projection)
        assert SHIP_SHARE in projection.summary.benefits
        assert WEAPON in projection.summary.benefits
        assert projection.summary.career_terms[-1].require_muster_out().benefits == [SHIP_SHARE, WEAPON]

    def test_apply_handles_mixed_sub_benefits(self):
        projection = _projection_with_term({Chars.SOC: 5})
        combined = CombinedBenefit(
            benefits=[
                CharacteristicIncrease(char=Chars.SOC, amount=1),
                YACHT,
            ]
        )
        combined.apply(projection)
        assert projection.summary.characteristics[Chars.SOC] == 6
        assert YACHT in projection.summary.benefits
        assert projection.summary.career_terms[-1].require_muster_out().benefits == [YACHT]

    def test_choice_benefit_option_can_be_combined(self):
        # ChoiceBenefit itself can reference combined as an option? No —
        # verify CombinedBenefit is part of AnyBenefit discriminated union.
        from pydantic import TypeAdapter

        from ceres.character.domain.benefits import AnyBenefit

        ta = TypeAdapter(AnyBenefit)
        data = {
            'type': CombinedBenefit.model_fields['type'].default,
            'benefits': [
                {'type': ItemBenefit.model_fields['type'].default, 'key': 'ship_share', 'label': 'Ship Share'}
            ],
        }
        result = ta.validate_python(data)
        assert isinstance(result, CombinedBenefit)
