from .spec import ExpenseRow


class ShipExpenses:
    def __init__(self, ship) -> None:
        self.ship = ship

    @property
    def production_cost(self) -> float:
        craft_cost = 0.0
        if self.ship.craft is not None:
            for docking_space in self.ship.craft._all_parts():
                craft_cost += docking_space.craft.cost
        cargo_holds = [] if self.ship.cargo is None else self.ship.cargo.cargo_holds
        cargo_hold_cost = sum(cargo_hold.crane_cost(self.ship) for cargo_hold in cargo_holds)
        software_cost = 0.0
        if self.ship.computer is not None:
            software_cost = sum(package.cost for package in self.ship.computer.software_packages.values())
        return (
            self.ship.hull_cost
            + self.ship.hull.radiation_shielding_cost(self.ship.displacement)
            + sum(part.cost for part in self.ship._all_parts())
            + software_cost
            + craft_cost
            + cargo_hold_cost
        )

    @property
    def sales_price_new(self) -> float:
        return self.production_cost * self.ship.design_type.cost_multiplier

    @property
    def mortgage(self) -> float:
        return round(self.sales_price_new / 240, 2)

    @property
    def maintenance(self) -> float:
        return float(round(self.sales_price_new / 12_000))

    @property
    def life_support(self) -> float:
        return self.life_support_facilities + self.life_support_people

    @property
    def life_support_facilities(self) -> float:
        if self.ship.command is not None and self.ship.command.cockpit is not None:
            return 0.0
        if self.ship.habitation is None:
            return 0.0
        return self.ship.habitation.fixed_life_support_cost(self.ship)

    @property
    def life_support_people(self) -> float:
        if self.ship.command is not None and self.ship.command.cockpit is not None:
            return 0.0
        if self.ship.habitation is None:
            return 0.0
        passenger_vector = self.ship.habitation.passenger_vector(self.ship)
        low_passage = passenger_vector.get('low', 0)
        low_berth_life_support = low_passage * 100
        return low_berth_life_support + self.ship.habitation.variable_life_support_cost(self.ship)

    @property
    def fuel(self) -> float:
        if self.ship.fuel is None:
            return 0.0

        has_jump_drive = self.ship.drives is not None and self.ship.drives.j_drive is not None
        has_fuel_scoops = self.ship.fuel.fuel_scoops is not None
        has_fuel_processor = self.ship.fuel.fuel_processor is not None

        cost = 0.0
        if self.ship.fuel.jump_fuel is not None:
            if not (has_fuel_scoops and has_fuel_processor):
                cost += self.ship.fuel.jump_fuel.tons * 2 * 500

        if self.ship.fuel.operation_fuel is not None:
            monthly_tons = self.ship.fuel.operation_fuel.tons * (4 / self.ship.fuel.operation_fuel.weeks)
            if has_jump_drive:
                if not (has_fuel_scoops and has_fuel_processor):
                    cost += monthly_tons * 500
            elif not has_fuel_scoops:
                cost += monthly_tons * 100

        return float(cost)

    @property
    def crew_salaries(self) -> float:
        return self.ship._crew_salary_cost()

    @property
    def total(self) -> float:
        return self.mortgage + self.maintenance + self.life_support + self.crew_salaries + self.fuel

    @property
    def rows(self) -> list[ExpenseRow]:
        return [
            ExpenseRow('Production Cost', self.production_cost),
            ExpenseRow('Sales Price New', self.sales_price_new),
            ExpenseRow('Mortgage', self.mortgage),
            ExpenseRow('Maintenance', self.maintenance),
            ExpenseRow('Life Support Facilities', self.life_support_facilities),
            ExpenseRow('Life Support People', self.life_support_people),
            ExpenseRow('Fuel', self.fuel),
            ExpenseRow('Crew Salaries', self.crew_salaries),
            ExpenseRow('Total Expenses', self.total),
        ]
