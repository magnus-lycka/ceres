from .spec import ExpenseRow


def production_cost(ship) -> float:
    craft_cost = 0.0
    if ship.craft is not None and ship.craft.docking_space is not None:
        craft_cost += ship.craft.docking_space.craft.cost
    cargo_holds = [] if ship.cargo is None else ship.cargo.cargo_holds
    cargo_hold_cost = sum(cargo_hold.crane_cost(ship) for cargo_hold in cargo_holds)
    software_cost = 0.0
    if ship.computer is not None:
        software_cost = sum(package.cost for package in ship.computer.software_packages.values())
    return ship.hull_cost + sum(part.cost for part in ship._all_parts()) + software_cost + craft_cost + cargo_hold_cost


def sales_price_new(ship) -> float:
    return production_cost(ship) * ship.design_type.cost_multiplier


def mortgage_cost(ship) -> float:
    return round(sales_price_new(ship) / 240, 2)


def maintenance_cost(ship) -> float:
    return float(round(sales_price_new(ship) / 12_000))


def life_support_cost(ship) -> float:
    if ship.command is not None and ship.command.cockpit is not None:
        return 0.0
    if ship.habitation is not None and ship.habitation.staterooms is not None:
        return ship.habitation.staterooms.life_support_cost
    return 0.0


def fuel_cost(ship) -> float:
    if ship.fuel is None or ship.fuel.jump_fuel is None:
        return 0.0
    fuel_cost_per_ton = 100 if ship.fuel.fuel_processor is not None else 500
    return float(ship.fuel.jump_fuel.tons * 2 * fuel_cost_per_ton)


def total_expenses(ship) -> float:
    return (
        mortgage_cost(ship)
        + maintenance_cost(ship)
        + life_support_cost(ship)
        + ship._crew_salary_cost()
        + fuel_cost(ship)
    )


def expense_rows(ship) -> list[ExpenseRow]:
    return [
        ExpenseRow('Production Cost', production_cost(ship)),
        ExpenseRow('Sales Price New', sales_price_new(ship)),
        ExpenseRow('Mortgage', mortgage_cost(ship)),
        ExpenseRow('Maintenance', maintenance_cost(ship)),
        ExpenseRow('Life Support', life_support_cost(ship)),
        ExpenseRow('Fuel', fuel_cost(ship)),
        ExpenseRow('Crew Salaries', ship._crew_salary_cost()),
        ExpenseRow('Total Expenses', total_expenses(ship)),
    ]
