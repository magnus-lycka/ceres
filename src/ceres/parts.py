from typing import Any, Optional, Union, ClassVar, TYPE_CHECKING

from pydantic import BaseModel, Field, field_validator, model_validator, PrivateAttr

if TYPE_CHECKING:
    from .ship import Ship

Number = Union[int, float]


class FloatModel(BaseModel):
    value: float | None = None
    _owner: Optional["ShipPart"] = PrivateAttr(default=None)
    model_config = {"frozen": True}

    def bind(self, owner: ShipPart) -> None:
        self._owner = owner

    @property
    def owner(self) -> "ShipPart":
        if self._owner is None:
            raise RuntimeError(f"{self.__class__.__name__} not bound to a ShipPart")
        return self._owner

    def resolve(self) -> float:
        return NotImplemented

    def __float__(self) -> float:
        return self.resolve()

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

    def __div__(self, other: Number) -> float:
        return self.resolve() / float(other)

    def __rdiv__(self, other: Number) -> float:
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


class TechLevel(BaseModel):
    value: int | None = None
    _owner: Optional["ShipPart"] = PrivateAttr(default=None)
    model_config = {"frozen": True}

    def bind(self, owner: ShipPart) -> None:
        self._owner = owner

    @property
    def owner(self) -> "ShipPart":
        if self._owner is None:
            raise RuntimeError(f"{self.__class__.__name__} not bound to a ShipPart")
        return self._owner

    def resolve(self) -> int:
        # Default to and compare with ships TL
        if self.value is not None:
            if self.owner.ship_tl < self.value:
                raise ValueError("Part TL can't be higher than Ship TL.")
            return self.value
        return self.owner.ship_tl

    def __eq__(self, other: object):
        if not isinstance(other, int):
            return NotImplemented
        return self.resolve() == other

    def __ne__(self, other: object):
        if not isinstance(other, int):
            return NotImplemented
        return self.resolve() != other

    def __ge__(self, other: int):
        return self.resolve() >= other

    def __gt__(self, other: int):
        return self.resolve() > other

    def __le__(self, other: int):
        return self.resolve() <= other

    def __lt__(self, other: int):
        return self.resolve() < other

    def __add__(self, other: Number) -> int:
        return self.resolve() + int(other)

    def __radd__(self, other: Number) -> int:
        return int(other) + self.resolve()

    def __sub__(self, other: Number) -> int:
        return self.resolve() - int(other)

    def __rsub__(self, other: Number) -> int:
        return int(other) - self.resolve()

    def __int__(self) -> int:
        return int(self.resolve())


class ShipPart(BaseModel):
    tl: TechLevel = Field(default_factory=TechLevel)
    cost: Cost = Field(default_factory=Cost)
    power: Power = Field(default_factory=Power)
    tons: Tons = Field(default_factory=Tons)
    _explicit_cost: ClassVar[bool] = True
    _explicit_power: ClassVar[bool] = True
    _explicit_tons: ClassVar[bool] = True
    _owner: Optional["Ship"] = PrivateAttr(default=None)
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
            raise ValueError(f"cost is derived for {cls.__name__}")
        return data

    @model_validator(mode="before")
    @classmethod
    def forbid_tons(cls, data):
        if "tons" in data and not cls._explicit_tons:
            raise ValueError(f"tons is derived for {cls.__name__}")
        return data

    @model_validator(mode="before")
    @classmethod
    def forbid_power(cls, data):
        if "power" in data and not cls._explicit_power:
            raise ValueError(f"power is derived for {cls.__name__}")
        return data

    @field_validator("tl", mode="before")
    @classmethod
    def _wrap_tl(cls, v):
        if isinstance(v, TechLevel):
            tl = v
        elif isinstance(v, int):
            tl = TechLevel(value=v)
        else:
            raise TypeError(f"Expected TechLevel or int, got {type(v)!r}")
        return tl

    @field_validator("cost", mode="before")
    @classmethod
    def _wrap_cost(cls, v):
        if isinstance(v, Cost):
            cost = v
        elif isinstance(v, (int, float)):
            cost = Cost(value=float(v))
        else:
            raise TypeError(f"Expected Cost or number, got {type(v)!r}")
        return cost

    @field_validator("power", mode="before")
    @classmethod
    def _wrap_power(cls, v):
        if isinstance(v, Power):
            power = v
        elif isinstance(v, (int, float)):
            power = Power(value=float(v))
        else:
            raise TypeError(f"Expected Power or number, got {type(v)!r}")
        return power

    @field_validator("tons", mode="before")
    @classmethod
    def _wrap_tons(cls, v):
        if isinstance(v, Tons):
            tons = v
        elif isinstance(v, (int, float)):
            tons = Tons(value=v)
        else:
            raise TypeError(f"Expected Tons or number, got {type(v)!r}")
        return tons

    def model_post_init(self, __context: Any) -> None:
        self.cost.bind(self)
        self.power.bind(self)
        self.tons.bind(self)
        self.tl.bind(self)

    def register_parts(self, container: set):
        container.add(self)

    def bind(self, owner: Ship) -> None:
        self._owner = owner
        # Provoke value errors relying on binding to ship
        int(self.cost)
        int(self.power)
        int(self.tons)
        int(self.tl)

    @property
    def owner(self) -> "Ship":
        if self._owner is None:
            raise RuntimeError(f"{self.__class__.__name__} not bound to a Ship")
        return self._owner

    @property
    def ship_tl(self):
        return self.owner.tl
