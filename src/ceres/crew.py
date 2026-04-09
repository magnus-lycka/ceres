import math

from .base import CeresModel
from .spec import CrewRow as SpecCrewRow

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


class CrewRole(CeresModel):
    role: str
    count: int
    monthly_salary: int

    @property
    def total_salary(self) -> int:
        return self.count * self.monthly_salary


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
        if ship.drives.jump_drive is not None:
            tons += ship.drives.jump_drive.tons
    if ship.power is not None and ship.power.fusion_plant is not None:
        tons += ship.power.fusion_plant.tons
    return tons


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


def _commercial_roles(ship) -> list[CrewRole]:
    if ship.displacement <= 100 and (ship.drives is None or ship.drives.jump_drive is None):
        return [CrewRole(role='PILOT', count=1, monthly_salary=PILOT_SALARY)]

    roles: list[CrewRole] = [CrewRole(role='PILOT', count=1, monthly_salary=PILOT_SALARY)]

    if ship.drives is not None and ship.drives.jump_drive is not None:
        roles.append(CrewRole(role='ASTROGATOR', count=1, monthly_salary=ASTROGATOR_SALARY))

    engineer_count = math.ceil(_drives_and_power_tonnage(ship) / 35) if _drives_and_power_tonnage(ship) > 0 else 0
    engineer_count = _apply_large_ship_reduction(ship, engineer_count)
    if engineer_count:
        roles.append(CrewRole(role='ENGINEER', count=engineer_count, monthly_salary=ENGINEER_SALARY))

    maintenance_count = _apply_large_ship_reduction(ship, ship.displacement // 1_000)
    if maintenance_count:
        roles.append(CrewRole(role='MAINTENANCE', count=maintenance_count, monthly_salary=MAINTENANCE_SALARY))

    gunner_count = _commercial_gunner_count(ship)
    gunner_count = _apply_large_ship_reduction(ship, gunner_count)
    if gunner_count:
        roles.append(CrewRole(role='GUNNER', count=gunner_count, monthly_salary=GUNNER_SALARY))

    administrator_count = _apply_large_ship_reduction(ship, ship.displacement // 2_000)
    if administrator_count:
        roles.append(CrewRole(role='ADMINISTRATOR', count=administrator_count, monthly_salary=ADMINISTRATOR_SALARY))

    sensor_operator_count = _apply_large_ship_reduction(ship, ship.displacement // 7_500)
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
    if medic_count:
        roles.append(CrewRole(role='MEDIC', count=medic_count, monthly_salary=MEDIC_SALARY))

    total_crew = sum(role.count for role in roles)
    officer_count = total_crew // 20
    if officer_count:
        roles.append(CrewRole(role='OFFICER', count=officer_count, monthly_salary=OFFICER_SALARY))

    return roles


def _military_roles(ship) -> list[CrewRole]:
    roles: list[CrewRole] = [CrewRole(role='PILOT', count=3, monthly_salary=PILOT_SALARY)]

    if ship.drives is not None and ship.drives.jump_drive is not None:
        roles.append(CrewRole(role='ASTROGATOR', count=1, monthly_salary=ASTROGATOR_SALARY))

    engineer_count = math.ceil(_drives_and_power_tonnage(ship) / 35) if _drives_and_power_tonnage(ship) > 0 else 0
    engineer_count = _apply_large_ship_reduction(ship, engineer_count)
    if engineer_count:
        roles.append(CrewRole(role='ENGINEER', count=engineer_count, monthly_salary=ENGINEER_SALARY))

    maintenance_count = _apply_large_ship_reduction(ship, ship.displacement // 500)
    if maintenance_count:
        roles.append(CrewRole(role='MAINTENANCE', count=maintenance_count, monthly_salary=MAINTENANCE_SALARY))

    gunner_count = _military_gunner_count(ship)
    gunner_count = _apply_large_ship_reduction(ship, gunner_count)
    if gunner_count:
        roles.append(CrewRole(role='GUNNER', count=gunner_count, monthly_salary=GUNNER_SALARY))

    administrator_count = _apply_large_ship_reduction(ship, ship.displacement // 1_000)
    if administrator_count:
        roles.append(CrewRole(role='ADMINISTRATOR', count=administrator_count, monthly_salary=ADMINISTRATOR_SALARY))

    sensor_operator_count = _apply_large_ship_reduction(ship, (ship.displacement // 7_500) * 3)
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


def crew_salary_cost(ship) -> float:
    return float(sum(role.total_salary for role in required_crew_roles(ship)))


def spec_crew_rows(ship) -> list[SpecCrewRow]:
    rows: list[SpecCrewRow] = []
    for role in required_crew_roles(ship):
        rows.append(
            SpecCrewRow(
                role=role.role,
                quantity=role.count if role.count > 1 else None,
                salary=role.total_salary,
            )
        )
    return rows
