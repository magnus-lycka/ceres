"""Approval snapshots for ship internal systems.

Snapshot 1 (test_system_table_values): all systems' tons/cost/power at TL15/400t.
Snapshot 2 (test_complex_system_spec_rows): spec rows for systems with rich notes/behavior.
Snapshot 3 (test_re_entry_systems): re-entry capability table + spec rows.
"""

import pytest

from ceres.make.ship import hull, ship
from ceres.make.ship.base import ShipBase
from ceres.make.ship.systems import (
    AccelerationBench,
    AccelerationSeat,
    AdvancedProbeDrones,
    AdvancedPsionicShielding,
    Aerofins,
    Airlock,
    Armoury,
    AssaultReEntryCapsule,
    BasicAutodoc,
    BasicReEntryCapsule,
    Biosphere,
    BoobyTrapTL6,
    BoobyTrapTL8,
    BoobyTrapTL10,
    BoobyTrapTL12,
    BreachingTube,
    Brewery,
    BriefingRoom,
    CommandBridge,
    CommercialZone,
    CommonArea,
    ConstructionDeck,
    ForcedLinkageApparatus,
    GourmetKitchen,
    GravityWellGenerator,
    GravScreen,
    HighSurvivabilityReEntryCapsule,
    HolographicHull,
    HotTub,
    JumpFilter,
    Laboratory,
    LibraryFacility,
    MedicalBay,
    MiningDrones,
    MultiEnvironmentSpace,
    ProbeDrones,
    PsionicShielding,
    ReEntryPod,
    RepairDrones,
    SwimmingPool,
    SystemsSection,
    Theatre,
    TrainingFacility,
    UNREPSystem,
    Vault,
    WetBar,
    Workshop,
    ZeroGRoom,
)
from tests.approval.snapshot import AnnotatedJSONSnapshotExtension, AnnotatedSnapshot


class _Ship(ShipBase):
    def __init__(self, tl=15, displacement=400):
        super().__init__(tl=tl, displacement=displacement)

    def remaining_usable_tonnage(self) -> float:
        return float(self.displacement)


def _bind(part, tl=15, displacement=400):
    part.bind(_Ship(tl, displacement))
    return part


def _row(part) -> dict:
    return {'tons': part.tons, 'cost': part.cost, 'power': part.power}


@pytest.mark.approval
def test_system_table_values(snapshot):
    """All ship systems — tons, cost, power at TL15/400-ton ship."""
    snap = AnnotatedSnapshot(
        {
            'Workshop': _row(_bind(Workshop())),
            'Laboratory': _row(_bind(Laboratory())),
            'LibraryFacility': _row(_bind(LibraryFacility())),
            'BriefingRoom': _row(_bind(BriefingRoom())),
            'CommandBridge': _row(_bind(CommandBridge())),
            'Armoury': _row(_bind(Armoury())),
            'WetBar': _row(_bind(WetBar())),
            'MedicalBay': _row(_bind(MedicalBay())),
            'MedicalBay_with_autodoc': _row(_bind(MedicalBay(autodoc=BasicAutodoc()))),
            'GravScreen': _row(_bind(GravScreen())),
            'GravityWellGenerator': _row(_bind(GravityWellGenerator())),
            'JumpFilter': _row(_bind(JumpFilter())),
            'PsionicShielding': _row(_bind(PsionicShielding())),
            'AdvancedPsionicShielding': _row(_bind(AdvancedPsionicShielding())),
            'AccelerationBench': _row(_bind(AccelerationBench())),
            'AccelerationSeat': _row(_bind(AccelerationSeat())),
            'Brewery_20L': _row(_bind(Brewery(litres_per_week=20), tl=10)),
            'GourmetKitchen_4': _row(_bind(GourmetKitchen(diners=4))),
            'BasicReEntryCapsule': _row(_bind(BasicReEntryCapsule())),
            'AssaultReEntryCapsule': _row(_bind(AssaultReEntryCapsule())),
            'HighSurvivabilityReEntryCapsule': _row(_bind(HighSurvivabilityReEntryCapsule())),
            'ReEntryPod': _row(_bind(ReEntryPod())),
            'Airlock_3': _row(_bind(Airlock(size=3.0), displacement=99)),
            'Aerofins': _row(_bind(Aerofins())),
            'BreachingTube': _row(_bind(BreachingTube())),
            'ForcedLinkage_Basic': _row(_bind(ForcedLinkageApparatus(tier='Basic'))),
            'ForcedLinkage_Improved': _row(_bind(ForcedLinkageApparatus(tier='Improved'))),
            'ForcedLinkage_Enhanced': _row(_bind(ForcedLinkageApparatus(tier='Enhanced'))),
            'ForcedLinkage_Advanced': _row(_bind(ForcedLinkageApparatus(tier='Advanced'))),
            'HolographicHull': _row(_bind(HolographicHull())),
            'HotTub_2': _row(_bind(HotTub(users=2))),
            'ProbeDrones_10': _row(_bind(ProbeDrones(count=10))),
            'AdvancedProbeDrones_10': _row(_bind(AdvancedProbeDrones(count=10))),
            'RepairDrones': _row(_bind(RepairDrones())),
            'MiningDrones_10': _row(_bind(MiningDrones(count=10))),
            'TrainingFacility_2': _row(_bind(TrainingFacility(trainees=2))),
            'CommonArea_2': _row(_bind(CommonArea(tons=2.0))),
            'SwimmingPool_2': _row(_bind(SwimmingPool(tons=2.0))),
            'Theatre_2': _row(_bind(Theatre(tons=2.0))),
            'Theatre_2_advanced': _row(_bind(Theatre(tons=2.0, advanced=True))),
            'ZeroGRoom_2': _row(_bind(ZeroGRoom(tons=2.0))),
            'CommercialZone_240': _row(_bind(CommercialZone(tons=240.0))),
            'Biosphere_4': _row(_bind(Biosphere(tons=4.0))),
            'UNREPSystem_25': _row(_bind(UNREPSystem(tons=25.0))),
            'MultiEnvironmentSpace_40': _row(MultiEnvironmentSpace(covered_tons=40)),
            'ConstructionDeck_100': _row(_bind(ConstructionDeck(tons=100))),
        }
    )
    assert snap == snapshot(extension_class=AnnotatedJSONSnapshotExtension)


@pytest.mark.approval
def test_complex_system_spec_rows(snapshot):
    """Key systems with rich notes/behavior — Vault, ForcedLinkage, BreachingTube, HolographicHull, BoobyTrap."""
    vault_8 = Vault(tons=8)
    vault_40 = Vault(tons=40)
    forced = ForcedLinkageApparatus(tier='Enhanced')
    forced.bind(_Ship(12))

    vault_ship = ship.Ship(
        tl=12,
        displacement=200,
        hull=hull.Hull(configuration=hull.standard_hull),
        systems=SystemsSection(internal_systems=[Vault(tons=8)]),
    )
    fla_ship = ship.Ship(
        tl=12,
        displacement=200,
        hull=hull.Hull(configuration=hull.standard_hull),
        systems=SystemsSection(internal_systems=[ForcedLinkageApparatus(tier='Enhanced')]),
    )
    holo_ship = ship.Ship(
        tl=12,
        displacement=200,
        hull=hull.Hull(configuration=hull.standard_hull),
        systems=SystemsSection(internal_systems=[HolographicHull()]),
    )
    tube_ship = ship.Ship(
        tl=12,
        displacement=200,
        hull=hull.Hull(configuration=hull.standard_hull),
        systems=SystemsSection(internal_systems=[BreachingTube()]),
    )
    booby_ship = ship.Ship(
        tl=12,
        displacement=99,
        hull=hull.Hull(configuration=hull.standard_hull, airlocks=[Airlock(booby_trap=BoobyTrapTL12())]),
    )
    construction_ship = ship.Ship(
        tl=12,
        displacement=400,
        hull=hull.Hull(configuration=hull.standard_hull),
        systems=SystemsSection(internal_systems=[ConstructionDeck(tons=100)]),
    )

    vault_row = vault_ship.build_spec().row('Vault')
    fla_row = fla_ship.build_spec().row('Forced Linkage Apparatus (Enhanced)', section='Systems')
    holo_row = holo_ship.build_spec().row('Holographic Hull')
    tube_row = tube_ship.build_spec().row('Breaching Tube')
    booby_row = booby_ship.build_spec().row('Airlock (2 tons)')
    constr_row = construction_ship.build_spec().row('Construction Deck')

    snap = AnnotatedSnapshot(
        {
            'vault_8_armour': vault_8.content_armour,
            'vault_8_hull_points': vault_8.content_hull_points,
            'vault_40_armour': vault_40.content_armour,
            'vault_40_hull_points': vault_40.content_hull_points,
            'vault_row': {'tons': vault_row.tons, 'cost': vault_row.cost},
            'forced_linkage_tl': forced.tl,
            'forced_linkage_pilot_dm': forced.pilot_check_dm,
            'fla_row': {'tons': fla_row.tons, 'cost': fla_row.cost, 'infos': fla_row.notes.infos},
            'holo_row': {
                'tons': holo_row.tons,
                'cost': holo_row.cost,
                'power': holo_row.power,
                'infos': holo_row.notes.infos,
            },
            'tube_row': {'tons': tube_row.tons, 'cost': tube_row.cost, 'infos': tube_row.notes.infos},
            'booby_row': {'tons': booby_row.tons, 'cost': booby_row.cost, 'infos': booby_row.notes.infos},
            'construction_row': {
                'tons': constr_row.tons,
                'cost': constr_row.cost,
                'power': constr_row.power,
                'infos': constr_row.notes.infos,
            },
            'booby_trap_table': {
                'TL6': {
                    'tl': BoobyTrapTL6().tl,
                    'cost': BoobyTrapTL6().cost,
                    'damage': BoobyTrapTL6().damage_per_round,
                },
                'TL8': {
                    'tl': BoobyTrapTL8().tl,
                    'cost': BoobyTrapTL8().cost,
                    'damage': BoobyTrapTL8().damage_per_round,
                },
                'TL10': {
                    'tl': BoobyTrapTL10().tl,
                    'cost': BoobyTrapTL10().cost,
                    'damage': BoobyTrapTL10().damage_per_round,
                },
                'TL12': {
                    'tl': BoobyTrapTL12().tl,
                    'cost': BoobyTrapTL12().cost,
                    'damage': BoobyTrapTL12().damage_per_round,
                },
            },
        }
    )
    snap.annotate('vault_infos', str(vault_8.notes.infos))
    assert snap == snapshot(extension_class=AnnotatedJSONSnapshotExtension)


@pytest.mark.approval
def test_re_entry_systems(snapshot):
    """Re-entry system capability table — tl, capacity, protection, detection DM, attack DM."""
    re_ship = ship.Ship(
        tl=14,
        displacement=200,
        hull=hull.Hull(configuration=hull.standard_hull),
        systems=SystemsSection(internal_systems=[HighSurvivabilityReEntryCapsule(), ReEntryPod()]),
    )
    capsule_row = re_ship.build_spec().row('Re-entry Capsule (high-survivability)')
    pod_row = re_ship.build_spec().row('Re-entry Pod')

    snap = AnnotatedSnapshot(
        {
            'BasicReEntryCapsule': {
                'tl': BasicReEntryCapsule().tl,
                'capacity': BasicReEntryCapsule().capacity,
                'protection': BasicReEntryCapsule().protection,
                'detection_dm': BasicReEntryCapsule().detection_dm,
                'attack_dm': BasicReEntryCapsule().attack_dm,
            },
            'AssaultReEntryCapsule': {
                'tl': AssaultReEntryCapsule().tl,
                'capacity': AssaultReEntryCapsule().capacity,
                'protection': AssaultReEntryCapsule().protection,
                'detection_dm': AssaultReEntryCapsule().detection_dm,
                'attack_dm': AssaultReEntryCapsule().attack_dm,
            },
            'HighSurvivabilityReEntryCapsule': {
                'tl': HighSurvivabilityReEntryCapsule().tl,
                'capacity': HighSurvivabilityReEntryCapsule().capacity,
                'protection': HighSurvivabilityReEntryCapsule().protection,
                'detection_dm': HighSurvivabilityReEntryCapsule().detection_dm,
                'attack_dm': HighSurvivabilityReEntryCapsule().attack_dm,
            },
            'ReEntryPod': {
                'tl': ReEntryPod().tl,
                'capacity': ReEntryPod().capacity,
                'protection': ReEntryPod().protection,
                'detection_dm': ReEntryPod().detection_dm,
                'attack_dm': ReEntryPod().attack_dm,
            },
            'capsule_spec_row': {'tons': capsule_row.tons, 'cost': capsule_row.cost},
            'pod_spec_row': {'tons': pod_row.tons, 'cost': pod_row.cost},
        }
    )
    snap.annotate('capsule_infos', str(HighSurvivabilityReEntryCapsule().notes.infos))
    assert snap == snapshot(extension_class=AnnotatedJSONSnapshotExtension)
