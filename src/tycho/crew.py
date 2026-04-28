import math
from typing import Annotated, ClassVar, Literal

from pydantic import BaseModel, ConfigDict, Field, PrivateAttr

from .base import CeresModel, Note, NoteCategory
from .spec import CrewRow as SpecCrewRow
from .text import optional_count


def _salary_for_level(base_salary: int, level: int) -> int:
    return int(base_salary / 2 * (1 + level))


class CrewRole(BaseModel):
    model_config = ConfigDict(frozen=True)

    role: str
    level: int = Field(default=1, ge=1)
    base_salary: ClassVar[int]

    @property
    def monthly_salary(self) -> int:
        return _salary_for_level(self.base_salary, self.level)

    @property
    def total_salary(self) -> int:
        return self.monthly_salary

    @property
    def display_role(self) -> str:
        if self.level <= 1:
            return self.role
        return f'{self.role}-{self.level}'


class Captain(CrewRole):
    role: Literal['CAPTAIN'] = 'CAPTAIN'
    base_salary = 10_000


class Pilot(CrewRole):
    role: Literal['PILOT'] = 'PILOT'
    base_salary = 6_000


class Astrogator(CrewRole):
    role: Literal['ASTROGATOR'] = 'ASTROGATOR'
    base_salary = 5_000


class Engineer(CrewRole):
    role: Literal['ENGINEER'] = 'ENGINEER'
    base_salary = 4_000


class Maintenance(CrewRole):
    role: Literal['MAINTENANCE'] = 'MAINTENANCE'
    base_salary = 1_000


class GeneralCrew(CrewRole):
    role: Literal['GENERAL CREW'] = 'GENERAL CREW'
    base_salary = 1_000


class Marine(CrewRole):
    role: Literal['MARINE'] = 'MARINE'
    base_salary = 1_000


class Gunner(CrewRole):
    role: Literal['GUNNER'] = 'GUNNER'
    base_salary = 2_000


class Steward(CrewRole):
    role: Literal['STEWARD'] = 'STEWARD'
    base_salary = 2_000


class Administrator(CrewRole):
    role: Literal['ADMINISTRATOR'] = 'ADMINISTRATOR'
    base_salary = 1_500


class SensorOperator(CrewRole):
    role: Literal['SENSOR OPERATOR'] = 'SENSOR OPERATOR'
    base_salary = 4_000


class Medic(CrewRole):
    role: Literal['MEDIC'] = 'MEDIC'
    base_salary = 4_000


class Officer(CrewRole):
    role: Literal['OFFICER'] = 'OFFICER'
    base_salary = 5_000


type AnyCrewRole = Annotated[
    Captain
    | Pilot
    | Astrogator
    | Engineer
    | Maintenance
    | GeneralCrew
    | Marine
    | Gunner
    | Steward
    | Administrator
    | SensorOperator
    | Medic
    | Officer,
    Field(discriminator='role'),
]


class ShipCrew(CeresModel):
    roles: list[AnyCrewRole] = Field(default_factory=list)
    _ship = PrivateAttr(default=None)

    @property
    def count(self) -> int:
        return len(self.effective_roles)

    def bind(self, ship) -> None:
        self._ship = ship

    def _bound_ship(self):
        if self._ship is None:
            raise RuntimeError('ShipCrew must be bound to a Ship before derived crew logic can be used')
        return self._ship

    @property
    def recommended_roles(self) -> list[CrewRole]:
        ship = self._bound_ship()
        if ship.military:
            return self._military_roles(ship)
        return self._commercial_roles(ship)

    @property
    def effective_roles(self) -> list[CrewRole]:
        if self.roles:
            return list(self.roles)
        return self.recommended_roles

    @property
    def grouped_roles(self) -> list[tuple[CrewRole, int]]:
        grouped: dict[tuple[str, int], list] = {}
        order: list[tuple[str, int]] = []
        for role in self.effective_roles:
            key = (role.role, role.level)
            if key not in grouped:
                grouped[key] = [role, 0]
                order.append(key)
            grouped[key][1] += 1
        return [(grouped[key][0], grouped[key][1]) for key in order]

    def role_counts(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for role in self.effective_roles:
            counts[role.role] = counts.get(role.role, 0) + 1
        return counts

    @property
    def total_salary(self) -> float:
        return float(sum(role.total_salary for role in self.effective_roles))

    def spec_rows(self) -> list[SpecCrewRow]:
        rows: list[SpecCrewRow] = []
        for role, quantity in self.grouped_roles:
            rows.append(
                SpecCrewRow(
                    role=role.display_role,
                    quantity=optional_count(quantity),
                    salary=role.monthly_salary,
                )
            )
        return rows

    def comparison_notes(self) -> list[Note]:
        if not self.roles:
            return []

        notes: list[Note] = []
        provided: dict[str, int] = {}
        for role in self.roles:
            provided[role.role] = provided.get(role.role, 0) + 1
        required: dict[str, int] = {}
        for role in self.recommended_roles:
            required[role.role] = required.get(role.role, 0) + 1
        all_roles = sorted(set(required) | set(provided))
        for role in all_roles:
            required_count = required.get(role, 0)
            provided_count = provided.get(role, 0)
            if provided_count < required_count:
                notes.append(
                    Note(
                        category=NoteCategory.WARNING,
                        message=f'{role} below recommended count: {provided_count} < {required_count}',
                    )
                )
            elif provided_count > required_count:
                notes.append(
                    Note(
                        category=NoteCategory.INFO,
                        message=f'{role} above recommended count: {provided_count} > {required_count}',
                    )
                )
        return notes

    def refresh_notes(self) -> None:
        self.notes = self.comparison_notes()

    def _steward_roles(self, ship) -> list[CrewRole]:
        required_level = _steward_required_level(ship)
        if required_level == 0:
            return []

        counts_by_level: dict[int, int] = {}
        remaining = required_level
        while remaining > 0:
            level = min(3, remaining)
            counts_by_level[level] = counts_by_level.get(level, 0) + 1
            remaining -= level

        roles: list[CrewRole] = []
        for level in sorted(counts_by_level, reverse=True):
            roles.extend([Steward(level=level) for _ in range(counts_by_level[level])])
        return roles

    def _commercial_roles(self, ship) -> list[CrewRole]:
        if ship.displacement <= 100 and (ship.drives is None or ship.drives.j_drive is None):
            return [Pilot()]

        roles: list[CrewRole] = [Pilot() for _ in range(1 + _carried_small_craft_count(ship))]

        if ship.drives is not None and ship.drives.j_drive is not None:
            roles.append(Astrogator())

        engineering_tonnage = _drives_and_power_tonnage(ship)
        engineer_count = math.ceil(engineering_tonnage / 35) if engineering_tonnage > 0 else 0
        roles.extend([Engineer() for _ in range(_apply_large_ship_reduction(ship, engineer_count))])
        roles.extend(
            [Maintenance() for _ in range(_apply_large_ship_reduction(ship, _commercial_maintenance_count(ship)))]
        )

        gunner_count = _apply_large_ship_reduction(ship, _commercial_gunner_count(ship))
        roles.extend([Gunner() for _ in range(gunner_count)])
        roles.extend(self._steward_roles(ship))

        administrator_count = _apply_large_ship_reduction(ship, ship.displacement // 2_000)
        roles.extend([Administrator() for _ in range(administrator_count)])

        sensor_operator_count = _apply_large_ship_reduction(ship, _sensor_operator_count(ship, military=False))
        roles.extend([SensorOperator() for _ in range(sensor_operator_count)])

        medic_count = len(roles) // 120
        medical_bay = None if ship.systems is None else ship.systems.medical_bay
        if medical_bay is not None and medical_bay.autodoc is None:
            medic_count = max(medic_count, 1)
        roles.extend([Medic() for _ in range(medic_count)])

        officer_count = len(roles) // 20
        roles.extend([Officer() for _ in range(officer_count)])
        return roles

    def _military_roles(self, ship) -> list[CrewRole]:
        if ship.displacement <= 100 and (ship.drives is None or ship.drives.j_drive is None):
            return [Pilot()]

        roles: list[CrewRole] = [Captain()]
        roles.extend([Pilot() for _ in range(3 + _carried_small_craft_count(ship))])

        if ship.drives is not None and ship.drives.j_drive is not None:
            roles.append(Astrogator())

        engineering_tonnage = _drives_and_power_tonnage(ship)
        engineer_count = math.ceil(engineering_tonnage / 35) if engineering_tonnage > 0 else 0
        roles.extend([Engineer() for _ in range(_apply_large_ship_reduction(ship, engineer_count))])
        roles.extend(
            [Maintenance() for _ in range(_apply_large_ship_reduction(ship, _military_maintenance_count(ship)))]
        )

        gunner_count = _apply_large_ship_reduction(ship, _military_gunner_count(ship))
        roles.extend([Gunner() for _ in range(gunner_count)])
        roles.extend(self._steward_roles(ship))

        administrator_count = _apply_large_ship_reduction(ship, ship.displacement // 1_000)
        roles.extend([Administrator() for _ in range(administrator_count)])

        sensor_operator_count = _apply_large_ship_reduction(ship, _sensor_operator_count(ship, military=True))
        roles.extend([SensorOperator() for _ in range(sensor_operator_count)])

        medic_count = len(roles) // 120
        medical_bay = None if ship.systems is None else ship.systems.medical_bay
        if medical_bay is not None and medical_bay.autodoc is None:
            medic_count = max(medic_count, 1)
        roles.extend([Medic() for _ in range(medic_count)])

        officer_count = len(roles) // 10
        roles.extend([Officer() for _ in range(officer_count)])
        return roles


def _crew_reduction_multiplier(displacement: int) -> float:
    if displacement >= 100_000:
        return 0.33
    if displacement >= 50_000:
        return 0.5
    if displacement >= 20_000:
        return 0.67
    if displacement > 5_000:
        return 0.75
    return 1.0


def _apply_large_ship_reduction(ship, count: int) -> int:
    if count == 0:
        return 0
    multiplier = _crew_reduction_multiplier(ship.displacement)
    return math.ceil(count * multiplier)


def _drives_and_power_tonnage(ship) -> float:
    tons = 0.0
    if ship.drives is not None:
        if ship.drives.m_drive is not None:
            tons += ship.drives.m_drive.tons
        if ship.drives.j_drive is not None:
            tons += ship.drives.j_drive.tons
    if ship.power is not None and ship.power.fusion_plant is not None:
        tons += ship.power.fusion_plant.tons
    return tons


def _contained_small_craft_tonnage(ship) -> float:
    if ship.craft is None:
        return 0.0
    return float(
        sum(part.craft.shipping_size for part in ship.craft._all_parts() if getattr(part, 'craft', None) is not None)
    )


def _carried_small_craft_count(ship) -> int:
    if ship.craft is None:
        return 0
    return sum(1 for part in ship.craft._all_parts() if getattr(part, 'craft', None) is not None and part.craft.requires_pilot)


def _explicit_passenger_vector(ship) -> dict[str, int]:
    if ship.passenger_vector is None:
        return {}
    return {str(kind).lower(): int(count) for kind, count in ship.passenger_vector.items()}


def _commercial_gunner_count(ship) -> int:
    if ship.weapons is None:
        return 0
    return len(ship.weapons.turrets) + len(ship.weapons.barbettes)


def _military_gunner_count(ship) -> int:
    if ship.weapons is None:
        return 0
    return (
        len(ship.weapons.turrets) * 2
        + len(ship.weapons.barbettes) * 2
        + sum(bay.crew_required_military for bay in ship.weapons.bays)
    )


def _sensor_operator_count(ship, *, military: bool) -> int:
    if military:
        tonnage_based_count = math.ceil(ship.displacement / 7_500) * 3
    else:
        tonnage_based_count = ship.displacement // 7_500
    station_based_count = 0
    if ship.sensors.sensor_stations is not None:
        station_based_count = ship.sensors.sensor_stations.count + 1
    return max(tonnage_based_count, station_based_count)


def _commercial_maintenance_count(ship) -> int:
    tonnage = ship.displacement + _contained_small_craft_tonnage(ship)
    if tonnage < 1_000:
        return 0
    return math.ceil(tonnage / 1_000)


def _military_maintenance_count(ship) -> int:
    tonnage = ship.displacement + _contained_small_craft_tonnage(ship)
    if tonnage < 500:
        return 0
    return math.ceil(tonnage / 500)


def _steward_required_level(ship) -> int:
    passenger_vector = _explicit_passenger_vector(ship)
    high_passage = passenger_vector.get('high', 0)
    middle_passage = passenger_vector.get('middle', 0)
    if high_passage == 0 and middle_passage == 0:
        return 0
    return math.ceil((middle_passage + 10 * high_passage) / 100)
