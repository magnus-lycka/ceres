import math

from .base import CeresModel
from .spec import CrewRow as SpecCrewRow
from .text import optional_count

PILOT_SALARY = 6_000
ASTROGATOR_SALARY = 5_000
ENGINEER_SALARY = 4_000
MAINTENANCE_SALARY = 1_000
GUNNER_SALARY = 2_000
STEWARD_SALARY = 2_000
ADMINISTRATOR_SALARY = 1_500
SENSOR_OPERATOR_SALARY = 4_000
MEDIC_SALARY = 4_000
OFFICER_SALARY = 5_000
SALARY_BY_ROLE = {
    'CAPTAIN': 10_000,
    'PILOT': PILOT_SALARY,
    'ASTROGATOR': ASTROGATOR_SALARY,
    'ENGINEER': ENGINEER_SALARY,
    'MAINTENANCE': MAINTENANCE_SALARY,
    'GUNNER': GUNNER_SALARY,
    'STEWARD': STEWARD_SALARY,
    'ADMINISTRATOR': ADMINISTRATOR_SALARY,
    'SENSOR OPERATOR': SENSOR_OPERATOR_SALARY,
    'MEDIC': MEDIC_SALARY,
    'OFFICER': OFFICER_SALARY,
}


class CrewRole(CeresModel):
    role: str
    count: int
    monthly_salary: int
    skill_level: int = 1

    @property
    def total_salary(self) -> int:
        return self.count * self.monthly_salary

    @property
    def display_role(self) -> str:
        if self.skill_level <= 1:
            return self.role
        return f'{self.role} (Skill {self.skill_level})'


def _normalize_vector(vector) -> dict[str, int]:
    if vector is None:
        return {}
    return {str(role): int(count) for role, count in vector.items()}


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
    return float(sum(docking_space.craft.shipping_size for docking_space in ship.craft._all_parts()))


def _carried_small_craft_count(ship) -> int:
    if ship.craft is None:
        return 0
    return sum(1 for docking_space in ship.craft._all_parts() if docking_space.craft.requires_pilot)


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


def _salary_for_skill_level(base_salary: int, skill_level: int) -> int:
    return int(base_salary * (1 + 0.5 * (skill_level - 1)))


def _steward_required_level(ship) -> int:
    passenger_vector = _explicit_passenger_vector(ship)
    high_passage = passenger_vector.get('high', 0)
    middle_passage = passenger_vector.get('middle', 0)
    if high_passage == 0 and middle_passage == 0:
        return 0
    return math.ceil((middle_passage + 10 * high_passage) / 100)


def _steward_roles(ship) -> list[CrewRole]:
    required_level = _steward_required_level(ship)
    if required_level == 0:
        return []

    counts_by_skill: dict[int, int] = {}
    remaining = required_level
    while remaining > 0:
        skill_level = min(3, remaining)
        counts_by_skill[skill_level] = counts_by_skill.get(skill_level, 0) + 1
        remaining -= skill_level

    roles: list[CrewRole] = []
    for skill_level in sorted(counts_by_skill, reverse=True):
        roles.append(
            CrewRole(
                role='STEWARD',
                count=counts_by_skill[skill_level],
                monthly_salary=_salary_for_skill_level(STEWARD_SALARY, skill_level),
                skill_level=skill_level,
            )
        )
    return roles


def _commercial_roles(ship) -> list[CrewRole]:
    if ship.displacement <= 100 and (ship.drives is None or ship.drives.j_drive is None):
        return [CrewRole(role='PILOT', count=1, monthly_salary=PILOT_SALARY)]

    roles: list[CrewRole] = [
        CrewRole(
            role='PILOT',
            count=1 + _carried_small_craft_count(ship),
            monthly_salary=PILOT_SALARY,
        )
    ]

    if ship.drives is not None and ship.drives.j_drive is not None:
        roles.append(CrewRole(role='ASTROGATOR', count=1, monthly_salary=ASTROGATOR_SALARY))

    engineer_count = math.ceil(_drives_and_power_tonnage(ship) / 35) if _drives_and_power_tonnage(ship) > 0 else 0
    engineer_count = _apply_large_ship_reduction(ship, engineer_count)
    if engineer_count:
        roles.append(CrewRole(role='ENGINEER', count=engineer_count, monthly_salary=ENGINEER_SALARY))

    maintenance_count = _apply_large_ship_reduction(ship, _commercial_maintenance_count(ship))
    if maintenance_count:
        roles.append(CrewRole(role='MAINTENANCE', count=maintenance_count, monthly_salary=MAINTENANCE_SALARY))

    gunner_count = _commercial_gunner_count(ship)
    gunner_count = _apply_large_ship_reduction(ship, gunner_count)
    if gunner_count:
        roles.append(CrewRole(role='GUNNER', count=gunner_count, monthly_salary=GUNNER_SALARY))

    roles.extend(_steward_roles(ship))

    administrator_count = _apply_large_ship_reduction(ship, ship.displacement // 2_000)
    if administrator_count:
        roles.append(CrewRole(role='ADMINISTRATOR', count=administrator_count, monthly_salary=ADMINISTRATOR_SALARY))

    sensor_operator_count = _apply_large_ship_reduction(
        ship,
        _sensor_operator_count(ship, military=False),
    )
    if sensor_operator_count:
        roles.append(
            CrewRole(
                role='SENSOR OPERATOR',
                count=sensor_operator_count,
                monthly_salary=SENSOR_OPERATOR_SALARY,
            )
        )

    total_crew_before_medics_and_officers = sum(role.count for role in roles)
    medic_count = total_crew_before_medics_and_officers // 120
    medical_bay = None if ship.systems is None else ship.systems.medical_bay
    if medical_bay is not None and medical_bay.autodoc is None:
        medic_count = max(medic_count, 1)
    if medic_count:
        roles.append(CrewRole(role='MEDIC', count=medic_count, monthly_salary=MEDIC_SALARY))

    total_crew = sum(role.count for role in roles)
    officer_count = total_crew // 20
    if officer_count:
        roles.append(CrewRole(role='OFFICER', count=officer_count, monthly_salary=OFFICER_SALARY))

    return roles


def _military_roles(ship) -> list[CrewRole]:
    if ship.displacement <= 100 and (ship.drives is None or ship.drives.j_drive is None):
        return [CrewRole(role='PILOT', count=1, monthly_salary=PILOT_SALARY)]

    roles: list[CrewRole] = [CrewRole(role='CAPTAIN', count=1, monthly_salary=10_000)]
    roles.append(
        CrewRole(
            role='PILOT',
            count=3 + _carried_small_craft_count(ship),
            monthly_salary=PILOT_SALARY,
        )
    )

    if ship.drives is not None and ship.drives.j_drive is not None:
        roles.append(CrewRole(role='ASTROGATOR', count=1, monthly_salary=ASTROGATOR_SALARY))

    engineer_count = math.ceil(_drives_and_power_tonnage(ship) / 35) if _drives_and_power_tonnage(ship) > 0 else 0
    engineer_count = _apply_large_ship_reduction(ship, engineer_count)
    if engineer_count:
        roles.append(CrewRole(role='ENGINEER', count=engineer_count, monthly_salary=ENGINEER_SALARY))

    maintenance_count = _apply_large_ship_reduction(ship, _military_maintenance_count(ship))
    if maintenance_count:
        roles.append(CrewRole(role='MAINTENANCE', count=maintenance_count, monthly_salary=MAINTENANCE_SALARY))

    gunner_count = _military_gunner_count(ship)
    gunner_count = _apply_large_ship_reduction(ship, gunner_count)
    if gunner_count:
        roles.append(CrewRole(role='GUNNER', count=gunner_count, monthly_salary=GUNNER_SALARY))

    roles.extend(_steward_roles(ship))

    administrator_count = _apply_large_ship_reduction(ship, ship.displacement // 1_000)
    if administrator_count:
        roles.append(CrewRole(role='ADMINISTRATOR', count=administrator_count, monthly_salary=ADMINISTRATOR_SALARY))

    sensor_operator_count = _apply_large_ship_reduction(
        ship,
        _sensor_operator_count(ship, military=True),
    )
    if sensor_operator_count:
        roles.append(
            CrewRole(
                role='SENSOR OPERATOR',
                count=sensor_operator_count,
                monthly_salary=SENSOR_OPERATOR_SALARY,
            )
        )

    total_crew_before_medics_and_officers = sum(role.count for role in roles)
    medic_count = total_crew_before_medics_and_officers // 120
    medical_bay = None if ship.systems is None else ship.systems.medical_bay
    if medical_bay is not None and medical_bay.autodoc is None:
        medic_count = max(medic_count, 1)
    if medic_count:
        roles.append(CrewRole(role='MEDIC', count=medic_count, monthly_salary=MEDIC_SALARY))

    total_crew = sum(role.count for role in roles)
    officer_count = total_crew // 10
    if officer_count:
        roles.append(CrewRole(role='OFFICER', count=officer_count, monthly_salary=OFFICER_SALARY))

    return roles


def required_crew_roles(ship) -> list[CrewRole]:
    if ship.military:
        return _military_roles(ship)
    return _commercial_roles(ship)


def effective_crew_roles(ship) -> list[CrewRole]:
    if ship.crew_vector is None:
        return required_crew_roles(ship)

    crew_vector = _normalize_vector(ship.crew_vector)
    roles: list[CrewRole] = []
    for role, count in crew_vector.items():
        if role not in SALARY_BY_ROLE:
            raise ValueError(f'Unknown crew role: {role}')
        roles.append(CrewRole(role=role, count=count, monthly_salary=SALARY_BY_ROLE[role]))
    return roles


def crew_vector_warnings(ship) -> list[str]:
    if ship.crew_vector is None:
        return []

    warnings: list[str] = []
    provided = _normalize_vector(ship.crew_vector)
    required: dict[str, int] = {}
    for role in required_crew_roles(ship):
        required[role.role] = required.get(role.role, 0) + role.count
    for role, required_count in required.items():
        provided_count = provided.get(role, 0)
        if provided_count < required_count:
            warnings.append(f'{role} below recommended count: {provided_count} < {required_count}')
    return warnings


def crew_salary_cost(ship) -> float:
    return float(sum(role.total_salary for role in effective_crew_roles(ship)))


def spec_crew_rows(ship) -> list[SpecCrewRow]:
    rows: list[SpecCrewRow] = []
    for role in effective_crew_roles(ship):
        rows.append(
            SpecCrewRow(
                role=role.display_role,
                quantity=optional_count(role.count),
                salary=role.monthly_salary,
            )
        )
    return rows
