"""Shared test helpers for character tests."""

from ceres.adapters.travellermap import TravellerMapWorld

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
