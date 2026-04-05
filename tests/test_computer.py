from ceres.base import ShipBase
from ceres.computer import Computer5, Computer10, Computer15, Core40, Intellect, JumpControl2, Library, Manoeuvre


class DummyOwner(ShipBase):
    def __init__(self, tl, displacement):
        super().__init__(tl=tl, displacement=displacement)


def test_computer_5_cost():
    c = Computer5()
    c.bind(DummyOwner(12, 6))
    assert c.minimum_tl == 7
    assert c.ship_tl == 12
    assert c.effective_tl == 12
    assert c.processing == 5
    assert c.jump_control_processing == 5
    assert float(c.cost) == 30_000


def test_computer_10_cost():
    c = Computer10()
    c.bind(DummyOwner(12, 6))
    assert float(c.cost) == 160_000


def test_computer_15_cost():
    c = Computer15()
    c.bind(DummyOwner(12, 6))
    assert float(c.cost) == 2_000_000


def test_computer_tons_zero():
    c = Computer5()
    c.bind(DummyOwner(12, 6))
    assert float(c.tons) == 0


def test_computer_power_zero():
    c = Computer5()
    c.bind(DummyOwner(12, 6))
    assert c.power == 0


def test_computer_5_min_tl():
    c = Computer5()
    c.bind(DummyOwner(6, 100))
    assert ('error', 'Requires TL7, ship is TL6') in [
        (note.category.value, note.message) for note in c.notes
    ]


def test_computer_recomputes_cost_from_input():
    c = Computer5.model_validate({'cost': 999})
    c.bind(DummyOwner(12, 6))
    assert c.cost == 30_000


def test_computer_bis_increases_cost_and_jump_control_processing():
    c = Computer5(bis=True)
    c.bind(DummyOwner(12, 6))
    assert c.processing == 5
    assert c.jump_control_processing == 10
    assert c.cost == 45_000


def test_computer_fib_increases_cost():
    c = Computer5(fib=True)
    c.bind(DummyOwner(12, 6))
    assert c.cost == 45_000


def test_computer_bis_and_fib_double_cost():
    c = Computer5(bis=True, fib=True)
    c.bind(DummyOwner(12, 6))
    assert c.cost == 60_000


def test_core_40_hardware():
    c = Core40()
    c.bind(DummyOwner(12, 100))
    assert c.minimum_tl == 9
    assert c.processing == 40
    assert c.jump_control_processing == 40
    assert c.cost == 45_000_000


def test_included_software_packages():
    c = Computer5()
    c.bind(DummyOwner(12, 100))
    assert [type(package) for package in c.included_software] == [Library, Manoeuvre, Intellect]
    assert [package.cost for package in c.included_software] == [0.0, 0.0, 0.0]


def test_jump_control_2_data():
    p = JumpControl2()
    assert p.description == 'Jump Control/2'
    assert p.minimum_tl == 11
    assert p.bandwidth == 10
    assert p.cost == 200_000


def test_computer_5_cannot_run_jump_control_2():
    c = Computer5()
    c.bind(DummyOwner(12, 100))
    assert not c.can_run(JumpControl2())


def test_computer_5_bis_can_run_jump_control_2():
    c = Computer5(bis=True)
    c.bind(DummyOwner(12, 100))
    assert c.can_run(JumpControl2())
