from typing import Any

from pydantic import BaseModel, field_validator, PrivateAttr


class TechLevel(BaseModel):
    value: int | None = None
    _owner: ShipPart | None = PrivateAttr(default=None)
    model_config = {"frozen": True}

    def bind(self, owner: ShipPart) -> None:
        self._owner = owner

    @property
    def owner(self) -> ShipPart:
        if self._owner is None:
            raise RuntimeError("TechLevel not bound to a ShipPart")
        return self._owner

    def resolve(self) -> int:
        if self.value is not None:
            if self._owner is not None and self._owner.ship_tl < self.value:
                raise ValueError("Part TL can't be higher than Ship TL.")
            return self.value
        return int(self._owner.ship_tl)  # type: ignore[union-attr]

    def _coerce(self, other: int | TechLevel) -> int:
        return int(other) if isinstance(other, TechLevel) else other

    def __eq__(self, other: object):
        if isinstance(other, TechLevel):
            return self.resolve() == other.resolve()
        if not isinstance(other, int):
            return NotImplemented
        return self.resolve() == other

    def __ne__(self, other: object):
        if isinstance(other, TechLevel):
            return self.resolve() != other.resolve()
        if not isinstance(other, int):
            return NotImplemented
        return self.resolve() != other

    def __ge__(self, other: int | TechLevel):
        return self.resolve() >= self._coerce(other)

    def __gt__(self, other: int | TechLevel):
        return self.resolve() > self._coerce(other)

    def __le__(self, other: int | TechLevel):
        return self.resolve() <= self._coerce(other)

    def __lt__(self, other: int | TechLevel):
        return self.resolve() < self._coerce(other)

    def __add__(self, other: int | float) -> int:
        return self.resolve() + int(other)

    def __radd__(self, other: int | float) -> int:
        return int(other) + self.resolve()

    def __sub__(self, other: int | float) -> int:
        return self.resolve() - int(other)

    def __rsub__(self, other: int | float) -> int:
        return int(other) - self.resolve()

    def __int__(self) -> int:
        return int(self.resolve())

    def __repr__(self) -> str:
        return f"TechLevel({self.value})"


class ShipBase(BaseModel):
    """Minimal ship interface that ShipPart subclasses depend on."""
    tl: TechLevel
    displacement: int

    @field_validator("tl", mode="before")
    @classmethod
    def _wrap_tl(cls, v: Any) -> TechLevel:
        if isinstance(v, TechLevel):
            return v
        if isinstance(v, int):
            return TechLevel(value=v)
        if isinstance(v, dict):
            return TechLevel(**v)
        raise TypeError(f"Expected TechLevel or int, got {type(v)!r}")

    @property
    def ship_tl(self) -> TechLevel:
        return self.tl

    @property
    def armour_volume_modifier(self) -> float:
        return 1.0
