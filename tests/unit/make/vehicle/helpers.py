"""Shared setup for vehicle design tests."""

from typing import Any

from ceres.make.vehicle.types import VehicleType
from ceres.make.vehicle.vehicle import Vehicle


def a_vehicle(**kwargs: Any) -> Vehicle:
    """A TL12 ground vehicle of 20 Spaces, with whatever a test changes."""
    defaults: dict[str, Any] = {'name': 'Test', 'vehicle_type': VehicleType.GROUND_VEHICLE, 'spaces': 20, 'tl': 12}
    return Vehicle(**(defaults | kwargs))
