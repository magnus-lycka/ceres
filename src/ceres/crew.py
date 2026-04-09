from .base import CeresModel
from .spec import CrewRow as SpecCrewRow


class CrewRole(CeresModel):
    role: str
    count: int
    monthly_salary: int

    @property
    def total_salary(self) -> int:
        return self.count * self.monthly_salary


def required_crew_roles(ship) -> list[CrewRole]:
    if ship.displacement <= 100 and ship.drives is not None and ship.drives.jump_drive is not None:
        return [
            CrewRole(role='PILOT', count=1, monthly_salary=6_000),
            CrewRole(role='ASTROGATOR', count=1, monthly_salary=5_000),
            CrewRole(role='ENGINEER', count=1, monthly_salary=4_000),
        ]
    if ship.displacement <= 100:
        return [CrewRole(role='PILOT', count=1, monthly_salary=6_000)]
    return []


def crew_salary_cost(ship) -> float:
    return float(sum(role.total_salary for role in required_crew_roles(ship)))


def spec_crew_rows(ship) -> list[SpecCrewRow]:
    return [SpecCrewRow(role=role.role, salary=role.total_salary) for role in required_crew_roles(ship)]
