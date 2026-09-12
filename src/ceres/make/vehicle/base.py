from ceres.shared import Assembly


class VehicleBase(Assembly):
    """Minimal vehicle interface that installed options depend on."""

    spaces: int
