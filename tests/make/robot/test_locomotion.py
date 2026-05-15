import pytest

from ceres.make.robot.locomotion import (
    AeroplaneLocomotion,
    AquaticLocomotion,
    GravLocomotion,
    HovercraftLocomotion,
    LocomotionUnion,
    NoneLocomotion,
    ThrusterLocomotion,
    TracksLocomotion,
    VtolLocomotion,
    WalkerLocomotion,
    WheelsAtvLocomotion,
    WheelsLocomotion,
)


class TestLocomotionTable:
    """Verify rule data against refs/robot/05_locomotion.md."""

    @pytest.mark.parametrize(
        'loco_cls, tl, agility, endurance, cost_mult',
        [
            (NoneLocomotion, 5, None, 216, 1.0),
            (WheelsLocomotion, 5, 0, 72, 2.0),
            (WheelsAtvLocomotion, 5, 0, 72, 3.0),
            (TracksLocomotion, 5, -1, 72, 2.0),
            (GravLocomotion, 9, 1, 24, 20.0),
            (AeroplaneLocomotion, 5, 1, 12, 12.0),
            (AquaticLocomotion, 6, -2, 72, 4.0),
            (VtolLocomotion, 7, 0, 24, 14.0),
            (WalkerLocomotion, 8, 0, 72, 10.0),
            (HovercraftLocomotion, 7, 1, 24, 10.0),
            (ThrusterLocomotion, 7, 1, 2, 20.0),
        ],
    )
    def test_locomotion_values(self, loco_cls, tl, agility, endurance, cost_mult):
        loco = loco_cls()
        assert loco.required_tl == tl
        assert loco.agility == agility
        assert loco.base_endurance == endurance
        assert loco.cost_multiplier == cost_mult

    def test_none_is_stationary(self):
        loco = NoneLocomotion()
        assert loco.base_speed == 0
        assert loco.is_none_locomotion is True

    def test_wheels_not_none(self):
        loco = WheelsLocomotion()
        assert loco.is_none_locomotion is False

    def test_grav_has_flyer_trait(self):
        loco = GravLocomotion()
        names = [t.name for t in loco.locomotion_traits]
        assert 'Flyer' in names

    def test_tracks_has_atv_trait(self):
        loco = TracksLocomotion()
        names = [t.name for t in loco.locomotion_traits]
        assert 'ATV' in names

    def test_wheels_atv_has_atv_trait(self):
        loco = WheelsAtvLocomotion()
        names = [t.name for t in loco.locomotion_traits]
        assert 'ATV' in names

    def test_wheels_no_traits(self):
        loco = WheelsLocomotion()
        assert loco.locomotion_traits == ()


class TestLocomotionLabels:
    @pytest.mark.parametrize(
        'loco_cls, expected_label',
        [
            (NoneLocomotion, 'None'),
            (WheelsLocomotion, 'Wheels'),
            (WheelsAtvLocomotion, 'Wheels, ATV'),
            (TracksLocomotion, 'Tracks'),
            (GravLocomotion, 'Grav'),
            (AeroplaneLocomotion, 'Aeroplane'),
            (AquaticLocomotion, 'Aquatic'),
            (VtolLocomotion, 'VTOL'),
            (WalkerLocomotion, 'Walker'),
            (HovercraftLocomotion, 'Hovercraft'),
            (ThrusterLocomotion, 'Thruster'),
        ],
    )
    def test_all_labels(self, loco_cls, expected_label):
        assert loco_cls().label() == expected_label


class TestSpeedLabel:
    def test_none_speed_is_zero(self):
        assert NoneLocomotion().speed_label() == '0m'

    def test_wheels_speed_is_five(self):
        assert WheelsLocomotion().speed_label() == '5m'


class TestNoneLocomotionSlotsBonus:
    def test_size1_bonus(self):
        loco = NoneLocomotion()
        assert loco.slots_bonus(base_slots=1) == 1  # ceil(1*1.25)-1 = 1

    def test_size4_bonus(self):
        loco = NoneLocomotion()
        assert loco.slots_bonus(base_slots=8) == 2  # ceil(8*1.25)-8 = 2

    def test_wheels_no_bonus(self):
        loco = WheelsLocomotion()
        assert loco.slots_bonus(base_slots=16) == 0


class TestLocomotionDiscriminatedUnion:
    """JSON round-trip via the discriminated union."""

    def test_roundtrip_none(self):
        from pydantic import TypeAdapter

        adapter: TypeAdapter[LocomotionUnion] = TypeAdapter(LocomotionUnion)
        loco = NoneLocomotion()
        data = loco.model_dump()
        restored = adapter.validate_python(data)
        assert isinstance(restored, NoneLocomotion)
        assert restored.type == 'NONE'

    def test_roundtrip_wheels(self):
        from pydantic import TypeAdapter

        adapter: TypeAdapter[LocomotionUnion] = TypeAdapter(LocomotionUnion)
        loco = WheelsLocomotion()
        data = loco.model_dump()
        restored = adapter.validate_python(data)
        assert isinstance(restored, WheelsLocomotion)

    def test_roundtrip_grav(self):
        from pydantic import TypeAdapter

        adapter: TypeAdapter[LocomotionUnion] = TypeAdapter(LocomotionUnion)
        loco = GravLocomotion()
        json_str = loco.model_dump_json()
        restored = adapter.validate_json(json_str)
        assert isinstance(restored, GravLocomotion)


class TestTacticalSpeedReduction:
    """refs/robot/08_locomotion_modifications.md — Tactical Speed Reduction."""

    def test_default_no_reduction(self):
        loco = WheelsLocomotion()
        assert loco.speed_reduction == 0
        assert loco.effective_speed == 5
        assert loco.speed_label() == '5m'
        assert loco.base_endurance == 72.0
        assert loco.speed_cost_fraction == 0.0

    def test_one_metre_reduction_wheels(self):
        loco = WheelsLocomotion(speed_reduction=1)
        assert loco.effective_speed == 4
        assert loco.speed_label() == '4m'

    def test_endurance_increases_10_percent_per_metre(self):
        loco = WheelsLocomotion(speed_reduction=1)
        assert loco.base_endurance == pytest.approx(72 * 1.1)

    def test_two_metre_reduction(self):
        loco = WheelsLocomotion(speed_reduction=2)
        assert loco.effective_speed == 3
        assert loco.base_endurance == pytest.approx(72 * 1.2)

    def test_cost_fraction_per_metre(self):
        loco = WheelsLocomotion(speed_reduction=1)
        assert loco.speed_cost_fraction == pytest.approx(-0.1)

    def test_cost_fraction_two_metres(self):
        loco = WheelsLocomotion(speed_reduction=2)
        assert loco.speed_cost_fraction == pytest.approx(-0.2)

    def test_reduce_to_zero_speed_is_allowed(self):
        loco = WheelsLocomotion(speed_reduction=5)
        assert loco.effective_speed == 0
        assert loco.speed_label() == '0m'

    def test_cannot_reduce_below_zero_speed(self):
        with pytest.raises((ValueError, Exception)):
            WheelsLocomotion(speed_reduction=6)

    def test_none_locomotion_already_zero_cannot_reduce(self):
        with pytest.raises((ValueError, Exception)):
            NoneLocomotion(speed_reduction=1)

    def test_roundtrip_preserves_speed_reduction(self):
        from pydantic import TypeAdapter

        adapter: TypeAdapter[LocomotionUnion] = TypeAdapter(LocomotionUnion)
        loco = WheelsLocomotion(speed_reduction=1)
        restored = adapter.validate_json(loco.model_dump_json())
        assert isinstance(restored, WheelsLocomotion)
        assert restored.speed_reduction == 1


class TestLocomotionBaseGuard:
    def test_base_label_raises(self):
        import pytest

        from ceres.make.robot.locomotion import _LocomotionBase

        with pytest.raises(NotImplementedError):
            _LocomotionBase.label(WheelsLocomotion())
