from typing import Any, ClassVar

from pydantic import BaseModel, Field, field_validator, model_validator, PrivateAttr

from .base import ShipBase

Number = int | float


class FloatModel(BaseModel):
    value: float | None = None
    _owner: ShipPart | None = PrivateAttr(default=None)
    model_config = {"frozen": True}

    def bind(self, owner: ShipPart) -> None:
        self._owner = owner

    @property
    def owner(self) -> ShipPart:
        if self._owner is None:
            raise RuntimeError(f"{self.__class__.__name__} not bound to a ShipPart")
        return self._owner

    def resolve(self) -> float:
        return NotImplemented

    def __float__(self) -> float:
        return float(self.resolve())

    def __int__(self) -> int:
        return int(self.resolve())

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.resolve()})"

    def __add__(self, other: Number) -> float:
        return self.resolve() + float(other)

    def __radd__(self, other: Number) -> float:
        return float(other) + self.resolve()

    def __sub__(self, other: Number) -> float:
        return self.resolve() - float(other)

    def __rsub__(self, other: Number) -> float:
        return float(other) - self.resolve()

    def __mul__(self, other: Number) -> float:
        return self.resolve() * float(other)

    def __rmul__(self, other: Number) -> float:
        return float(other) * self.resolve()

    def __truediv__(self, other: Number) -> float:
        return self.resolve() / float(other)

    def __rtruediv__(self, other: Number) -> float:
        return float(other) / self.resolve()

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, (int, float)):
            return NotImplemented
        return self.resolve() == float(other)


class Cost(FloatModel):
    def resolve(self) -> float:
        if self.value is not None:
            return self.value
        return self.owner.calculate_cost()


class Power(FloatModel):
    def resolve(self) -> float:
        if self.value is not None:
            return self.value
        return self.owner.calculate_power()


class Tons(FloatModel):
    def resolve(self) -> float:
        if self.value is not None:
            return self.value
        return self.owner.calculate_tons()



class ShipPart(BaseModel):
    cost: Cost = Field(default_factory=Cost)
    power: Power = Field(default_factory=Power)
    tons: Tons = Field(default_factory=Tons)
    minimum_tl: ClassVar[int] = 0
    _explicit_cost: ClassVar[bool] = True
    _explicit_power: ClassVar[bool] = True
    _explicit_tons: ClassVar[bool] = True
    _owner: ShipBase | None = PrivateAttr(default=None)
    model_config = {"frozen": True}

    def calculate_cost(self) -> float:
        raise NotImplementedError

    def calculate_power(self) -> float:
        raise NotImplementedError

    def calculate_tons(self) -> float:
        raise NotImplementedError

    @model_validator(mode="before")
    @classmethod
    def forbid_cost(cls, data):
        if "cost" in data and not cls._explicit_cost:
            v = data["cost"]
            if isinstance(v, dict):
                v = v.get("value")
            if v is not None:
                raise ValueError(f"cost is derived for {cls.__name__}")
        return data

    @model_validator(mode="before")
    @classmethod
    def forbid_tons(cls, data):
        if "tons" in data and not cls._explicit_tons:
            v = data["tons"]
            if isinstance(v, dict):
                v = v.get("value")
            if v is not None:
                raise ValueError(f"tons is derived for {cls.__name__}")
        return data

    @model_validator(mode="before")
    @classmethod
    def forbid_power(cls, data):
        if "power" in data and not cls._explicit_power:
            v = data["power"]
            if isinstance(v, dict):
                v = v.get("value")
            if v is not None:
                raise ValueError(f"power is derived for {cls.__name__}")
        return data

    @field_validator("cost", mode="before")
    @classmethod
    def _wrap_cost(cls, v):
        if isinstance(v, Cost):
            return v
        if isinstance(v, (int, float)):
            return Cost(value=float(v))
        if isinstance(v, dict):
            return Cost(**v)
        raise TypeError(f"Expected Cost or number, got {type(v)!r}")

    @field_validator("power", mode="before")
    @classmethod
    def _wrap_power(cls, v):
        if isinstance(v, Power):
            return v
        if isinstance(v, (int, float)):
            return Power(value=float(v))
        if isinstance(v, dict):
            return Power(**v)
        raise TypeError(f"Expected Power or number, got {type(v)!r}")

    @field_validator("tons", mode="before")
    @classmethod
    def _wrap_tons(cls, v):
        if isinstance(v, Tons):
            return v
        if isinstance(v, (int, float)):
            return Tons(value=v)
        if isinstance(v, dict):
            return Tons(**v)
        raise TypeError(f"Expected Tons or number, got {type(v)!r}")

    def model_post_init(self, __context: Any) -> None:
        self.cost.bind(self)
        self.power.bind(self)
        self.tons.bind(self)

    def bind(self, owner: ShipBase) -> None:
        self._owner = owner
        self.validate_tl()
        int(self.cost)
        int(self.power)
        int(self.tons)

    @property
    def owner(self) -> ShipBase:
        if self._owner is None:
            raise RuntimeError(f"{self.__class__.__name__} not bound to a Ship")
        return self._owner

    @property
    def ship_tl(self) -> int:
        return self.owner.tl

    @property
    def effective_tl(self) -> int:
        return self.ship_tl

    def validate_tl(self) -> None:
        if self.ship_tl < self.minimum_tl:
            raise ValueError(
                f"{self.__class__.__name__} requires TL{self.minimum_tl}, "
                f"ship is TL{self.ship_tl}"
            )
