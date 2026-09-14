from pydantic import PrivateAttr

from ceres.shared import Assembly, CeresModel


class VehicleBase(Assembly):
    """Minimal vehicle interface that installed options depend on."""

    spaces: int


class InstalledInVehicle(CeresModel):
    """Something bound to the vehicle it is installed in.

    Binding follows ARCHITECTURE.md's two-phase construction: what the thing
    costs and occupies can depend on its vehicle, which it cannot know until the
    vehicle has been built.
    """

    _vehicle: VehicleBase | None = PrivateAttr(default=None)

    def bind(self, vehicle: VehicleBase) -> None:
        self._vehicle = vehicle

    @property
    def vehicle(self) -> VehicleBase:
        if self._vehicle is None:
            raise RuntimeError(f'{type(self).__name__} is not installed in a vehicle')
        return self._vehicle

    def __eq__(self, other: object) -> bool:
        # Two installed things are the same if they are the same thing; which
        # vehicle each happens to sit in is not part of that. Pydantic's own
        # comparison includes private attributes, and following the reference to
        # the vehicle leads straight back here.
        return type(self) is type(other) and self.__dict__ == other.__dict__

    # Mutable and compared by value, so not hashable.
    __hash__ = None
