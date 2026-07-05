"""Unit tests for systems/section.py — SystemsSection."""

from ceres.make.ship.spec import ShipSpec, SpecRow, SpecSection
from ceres.make.ship.systems.access import BreachingTube
from ceres.make.ship.systems.command import BriefingRoom, CommandBridge
from ceres.make.ship.systems.common_areas import CommercialZone
from ceres.make.ship.systems.drones import MiningDrones, ProbeDrones, RepairDrones
from ceres.make.ship.systems.facilities import Laboratory, LibraryFacility, TrainingFacility, Workshop
from ceres.make.ship.systems.medical import Biosphere, MedicalBay
from ceres.make.ship.systems.section import SystemsSection
from ceres.make.ship.systems.security import Armoury


class _Ship:
    def _grouped_spec_rows(self, section, parts):
        return [SpecRow(section=section, item=part.item_description()) for part in parts]

    def _spec_row_for_part(self, section, part):
        return SpecRow(section=section, item=part.item_description())


class TestSystemsSection:
    def test_empty_section_has_no_parts(self):
        section = SystemsSection()
        assert section.internal_systems == []

    def test_section_holds_heterogeneous_parts(self):
        section = SystemsSection(internal_systems=[Workshop(), BreachingTube()])
        assert len(section.internal_systems) == 2

    def test_typed_internal_system_accessors(self):
        armoury = Armoury()
        biosphere = Biosphere(tons=4)
        commercial_zone = CommercialZone(tons=10)
        medical_bay = MedicalBay()
        laboratory = Laboratory()
        library = LibraryFacility()
        briefing_room = BriefingRoom(tons=4)
        command_bridge = CommandBridge()
        training_facility = TrainingFacility(trainees=2)
        workshop = Workshop()
        section = SystemsSection(
            internal_systems=[
                armoury,
                biosphere,
                commercial_zone,
                medical_bay,
                laboratory,
                library,
                briefing_room,
                command_bridge,
                training_facility,
                workshop,
            ]
        )

        assert section.armouries == [armoury]
        assert section.biospheres == [biosphere]
        assert section.commercial_zones == [commercial_zone]
        assert section.medical_bays == [medical_bay]
        assert section.laboratories == [laboratory]
        assert section.libraries == [library]
        assert section.briefing_rooms == [briefing_room]
        assert section.command_bridges == [command_bridge]
        assert section.training_facilities == [training_facility]
        assert section.workshops == [workshop]

    def test_all_parts_includes_internal_systems_and_drones(self):
        workshop = Workshop()
        drones = RepairDrones()
        section = SystemsSection(internal_systems=[workshop], drones=[drones])
        assert section._all_parts() == [workshop, drones]

    def test_add_spec_rows_sets_quantities_for_counted_drone_systems(self):
        section = SystemsSection(
            internal_systems=[Workshop()],
            drones=[
                ProbeDrones(count=1),
                ProbeDrones(count=5),
                MiningDrones(count=3),
                RepairDrones(),
            ],
        )
        spec = ShipSpec()

        section.add_spec_rows(_Ship(), spec)

        rows = spec.rows_for_section(SpecSection.SYSTEMS)
        assert [row.item for row in rows] == [
            'Workshop',
            'Probe Drone',
            'Probe Drones',
            'Mining Drones',
            'Repair Drones',
        ]
        assert [row.quantity for row in rows] == [None, None, 5, 3, None]
