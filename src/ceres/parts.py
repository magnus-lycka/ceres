from pydantic import BaseModel, Field, computed_field


class ShipPart(BaseModel):
    tl: int
    cost_value: int | None = Field(default=None, alias="cost", repr=False)
    power_value: float | None = Field(default=None, alias="power", repr=False)
    tons_value: float | None = Field(default=None, alias="tons", repr=False)

    @computed_field
    @property
    def cost(self) -> int:
        if self.cost_value is None:
            raise ValueError("cost is derived in this subclass")
        return self.cost_value

    @computed_field
    @property
    def power(self) -> int:
        if self.power_value is None:
            raise ValueError("power is derived in this subclass")
        return self.power_value

    @computed_field
    @property
    def tons(self) -> int:
        if self.tons_value is None:
            raise ValueError("tons is derived in this subclass")
        return self.tons_value
        