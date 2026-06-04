"""Shared test helpers for character tests."""

from ceres.adapters.travellermap import TravellerMapWorld

MOCK_WORLD_2 = TravellerMapWorld.model_validate(
    {
        'Name': 'Regina',
        'Hex': '1910',
        'UWP': 'A788899-C',
        'PBG': '703',
        'Zone': '',
        'Bases': 'NW',
        'Allegiance': 'ImDd',
        'Stellar': 'F7 V',
        'SS': 'A',
        'Ix': '{ 4 }',
        'Ex': '(D7E+5)',
        'Cx': '[AC9G]',
        'Nobility': 'BcCeDfFe',
        'Worlds': 8,
        'ResourceUnits': 1116,
        'Subsector': 1,
        'Quadrant': 1,
        'WorldX': -50,
        'WorldY': -10,
        'Remarks': 'Ri Pa Ph An Cp (Spinward Marches) Sa',
        'LegacyBaseCode': 'NW',
        'Sector': 'Spinward Marches',
        'SubsectorName': 'Regina',
        'SectorAbbreviation': 'Spin',
        'AllegianceName': 'Third Imperium, Domain of Deneb',
    }
)

MOCK_WORLD = TravellerMapWorld.model_validate(
    {
        'Name': 'Hexx',
        'Hex': '2715',
        'UWP': 'B78A577-D',
        'PBG': '314',
        'Zone': '',
        'Bases': 'N',
        'Allegiance': 'ImDd',
        'Stellar': 'F6 V',
        'SS': 'H',
        'Ix': '{ 1 }',
        'Ex': '(C45+1)',
        'Cx': '[565D]',
        'Nobility': 'Bc',
        'Worlds': 11,
        'ResourceUnits': 240,
        'Subsector': 7,
        'Quadrant': 1,
        'WorldX': -102,
        'WorldY': -25,
        'Remarks': 'Ni Wa Pr Ht',
        'LegacyBaseCode': 'N',
        'Sector': 'Trojan Reach',
        'SubsectorName': 'Tobia',
        'SectorAbbreviation': 'Troj',
        'AllegianceName': 'Third Imperium, Domain of Deneb',
    }
)
