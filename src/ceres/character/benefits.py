"""Muster-out benefit types."""

from typing import Annotated, Literal

from pydantic import BaseModel, Field

from ceres.character.characteristics import Chars


class CharacteristicIncrease(BaseModel):
    type: Literal['characteristic'] = 'characteristic'
    char: Chars
    amount: int

    @property
    def display_label(self) -> str:
        return f'{self.char} +{self.amount}'

    @property
    def exceptional(self) -> bool:
        return False


class ItemBenefit(BaseModel):
    type: Literal['item'] = 'item'
    key: str
    label: str
    exceptional: bool = False

    @property
    def display_label(self) -> str:
        return self.label


class ChoiceBenefit(BaseModel):
    """A benefit where the player picks one of several options (e.g. 'SOC +1 or Cybernetic Implant')."""

    type: Literal['choice'] = 'choice'
    options: list[CharacteristicIncrease | ItemBenefit]

    @property
    def display_label(self) -> str:
        return ' or '.join(b.display_label for b in self.options)

    @property
    def exceptional(self) -> bool:
        return any(b.exceptional for b in self.options)


AnyBenefit = Annotated[CharacteristicIncrease | ItemBenefit | ChoiceBenefit, Field(discriminator='type')]

_BENEFIT_REGISTRY: dict[str, ItemBenefit] = {
    'ship_share': ItemBenefit(key='ship_share', label='Ship Share'),
    'scout_ship': ItemBenefit(key='scout_ship', label='Scout Ship', exceptional=True),
    'lab_ship': ItemBenefit(key='lab_ship', label='Lab Ship', exceptional=True),
    'free_trader': ItemBenefit(key='free_trader', label='Free Trader', exceptional=True),
    'yacht': ItemBenefit(key='yacht', label='Yacht', exceptional=True),
    'far_trader': ItemBenefit(key='far_trader', label='Far Trader', exceptional=True),
    'subsidised_merchant': ItemBenefit(key='subsidised_merchant', label='Subsidised Merchant', exceptional=True),
    'safari_ship': ItemBenefit(key='safari_ship', label='Safari Ship', exceptional=True),
    'tas_membership': ItemBenefit(key='tas_membership', label='TAS Membership'),
    'weapon': ItemBenefit(key='weapon', label='Weapon'),
    'scientific_equipment': ItemBenefit(key='scientific_equipment', label='Scientific Equipment'),
    'armor': ItemBenefit(key='armor', label='Armor'),
    'combat_implant': ItemBenefit(key='combat_implant', label='Combat Implant'),
    'cybernetic_implant': ItemBenefit(key='cybernetic_implant', label='Cybernetic Implant'),
}


def parse_benefit(s: str | list) -> AnyBenefit:
    """Parse a YAML benefit string (or list for a choice) into a typed benefit object."""
    if isinstance(s, list):
        options: list[CharacteristicIncrease | ItemBenefit] = []
        for item in s:
            benefit = parse_benefit(item)
            if isinstance(benefit, ChoiceBenefit):
                raise TypeError('Nested choice benefits are not supported')
            options.append(benefit)
        return ChoiceBenefit(options=options)
    parts = s.split('_')
    if len(parts) == 3 and parts[1] == 'plus' and parts[2].isdigit():
        return CharacteristicIncrease(char=Chars(parts[0].upper()), amount=int(parts[2]))
    if s in _BENEFIT_REGISTRY:
        return _BENEFIT_REGISTRY[s]
    label = ' '.join(word.capitalize() for word in parts)
    return ItemBenefit(key=s, label=label)


__all__ = ['AnyBenefit', 'CharacteristicIncrease', 'ChoiceBenefit', 'ItemBenefit', 'parse_benefit']
