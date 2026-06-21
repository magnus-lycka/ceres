"""DiceRoll: a parsed xDy dice expression."""

from pydantic import BaseModel, model_validator


class DiceRoll(BaseModel):
    count: int
    faces: int

    @model_validator(mode='before')
    @classmethod
    def _parse_string(cls, v: object) -> object:
        if not isinstance(v, str):
            return v
        lower = v.lower()
        if 'd' not in lower:
            raise ValueError(f'Invalid dice notation: {v!r}')
        left, right = lower.split('d', 1)
        count = int(left) if left else 1
        faces = int(right)
        return {'count': count, 'faces': faces}

    @classmethod
    def parse(cls, s: str) -> DiceRoll:
        return cls.model_validate(s)

    def roll_options(self) -> list[int]:
        return list(range(self.count, self.count * self.faces + 1))

    def __str__(self) -> str:
        if self.count == 1:
            return f'D{self.faces}'
        return f'{self.count}D{self.faces}'
