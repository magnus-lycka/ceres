"""Muster-out benefit types."""

from typing import Annotated, Literal, Protocol

from pydantic import BaseModel, Field

from ceres.character.domain.characteristics import Chars
from ceres.character.mechanism.event_base import PendingInputBase


class _BenefitSummary(Protocol):
    characteristics: dict[Chars, int]

    def add_muster_out_benefit(self, benefit: ItemBenefit) -> None: ...


class _BenefitProjection(Protocol):
    pending_inputs: list[PendingInputBase]

    @property
    def summary(self) -> _BenefitSummary: ...


class CharacteristicIncrease(BaseModel):
    kind: Literal['stat_benefit'] = 'stat_benefit'
    char: Chars
    amount: int

    @property
    def display_label(self) -> str:
        return f'{self.char} +{self.amount}'

    @property
    def exceptional(self) -> bool:
        return False

    def apply(self, projection: _BenefitProjection, event_id: int = 0) -> None:
        current = projection.summary.characteristics.get(self.char, 0)
        projection.summary.characteristics[self.char] = min(15, current + self.amount)


class ItemBenefit(BaseModel):
    kind: Literal['item_benefit'] = 'item_benefit'
    key: str
    label: str
    exceptional: bool = False

    @property
    def display_label(self) -> str:
        return self.label

    def apply(self, projection: _BenefitProjection, event_id: int = 0) -> None:
        projection.summary.add_muster_out_benefit(self)


class ChoiceBenefit(BaseModel):
    """A benefit where the player picks one of several options (e.g. 'SOC +1 or Cybernetic Implant')."""

    kind: Literal['option_benefit'] = 'option_benefit'
    options: list[CharacteristicIncrease | ItemBenefit]

    @property
    def display_label(self) -> str:
        return ' or '.join(b.display_label for b in self.options)

    @property
    def exceptional(self) -> bool:
        return any(b.exceptional for b in self.options)

    def apply(self, projection: _BenefitProjection, event_id: int = 0) -> None:
        from ceres.character.domain.career.career_events import PendingBenefitChoice

        projection.pending_inputs.append(
            PendingBenefitChoice(
                pending_id=(event_id, 0),
                instruction=f'Choose one benefit: {self.display_label}',
                benefit_options=list(self.options),
            )
        )


class CombinedBenefit(BaseModel):
    """Multiple benefits all granted together (e.g. 'SOC +1 and Yacht')."""

    kind: Literal['combined'] = 'combined'
    benefits: list[CharacteristicIncrease | ItemBenefit]

    @property
    def display_label(self) -> str:
        return ' and '.join(b.display_label for b in self.benefits)

    @property
    def exceptional(self) -> bool:
        return any(b.exceptional for b in self.benefits)

    def apply(self, projection: _BenefitProjection, event_id: int = 0) -> None:
        for sub_benefit in self.benefits:
            sub_benefit.apply(projection, event_id)


AnyBenefit = Annotated[
    CharacteristicIncrease | ItemBenefit | ChoiceBenefit | CombinedBenefit,
    Field(discriminator='kind'),
]

# Ships and vehicles
SCOUT_SHIP = ItemBenefit(key='scout_ship', label='Scout Ship', exceptional=True)
LAB_SHIP = ItemBenefit(key='lab_ship', label='Lab Ship', exceptional=True)
FREE_TRADER = ItemBenefit(key='free_trader', label='Free Trader', exceptional=True)
YACHT = ItemBenefit(key='yacht', label='Yacht', exceptional=True)
FAR_TRADER = ItemBenefit(key='far_trader', label='Far Trader', exceptional=True)
SUBSIDISED_MERCHANT = ItemBenefit(key='subsidised_merchant', label='Subsidised Merchant', exceptional=True)
SAFARI_SHIP = ItemBenefit(key='safari_ship', label='Safari Ship', exceptional=True)
PERSONAL_VEHICLE = ItemBenefit(key='personal_vehicle', label='Personal Vehicle')
SHIPS_BOAT = ItemBenefit(key='ships_boat', label="Ship's Boat")

# Financial instruments
SHIP_SHARE = ItemBenefit(key='ship_share', label='Ship Share')
TAS_MEMBERSHIP = ItemBenefit(key='tas_membership', label='TAS Membership')

# Weapons and armour
WEAPON = ItemBenefit(key='weapon', label='Weapon')
BLADE = ItemBenefit(key='blade', label='Blade')
GUN = ItemBenefit(key='gun', label='Gun')
ARMOR = ItemBenefit(key='armor', label='Armor')

# Implants
COMBAT_IMPLANT = ItemBenefit(key='combat_implant', label='Combat Implant')
CYBERNETIC_IMPLANT = ItemBenefit(key='cybernetic_implant', label='Cybernetic Implant')

# Equipment
SCIENTIFIC_EQUIPMENT = ItemBenefit(key='scientific_equipment', label='Scientific Equipment')

# Contacts
CONTACT = ItemBenefit(key='contact', label='Contact')
ALLY = ItemBenefit(key='ally', label='Ally')

# Prisoner career skill benefits
DECEPTION_ITEM = ItemBenefit(key='deception', label='Deception')
PERSUADE_ITEM = ItemBenefit(key='persuade', label='Persuade')
STEALTH_ITEM = ItemBenefit(key='stealth', label='Stealth')
MELEE_ITEM = ItemBenefit(key='melee', label='Melee')
RECON_ITEM = ItemBenefit(key='recon', label='Recon')
STREETWISE_ITEM = ItemBenefit(key='streetwise', label='Streetwise')
