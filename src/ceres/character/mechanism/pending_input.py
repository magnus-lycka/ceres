from typing import (
    TYPE_CHECKING,
    Any,
    ClassVar,
    Literal as _Literal,
    get_args,
    get_origin,
)

from pydantic import BaseModel

from ceres.character.input_specs import InputSpec

if TYPE_CHECKING:
    from ceres.character.mechanism.character_state import CharacterProjection


class ChoiceBase(BaseModel):
    """A self-addressed envelope: one option in a PendingChoices list, carries its own handler."""

    kind: str
    label: str = ''

    def handle(self, projection: Any, event: Any) -> None:
        raise NotImplementedError(f'{type(self).__name__}.handle() not implemented')


class PendingInputBase(BaseModel):
    _registry: ClassVar[dict[str, type[PendingInputBase]]] = {}

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        annotations: dict[str, Any] = {}
        for base in reversed(cls.__mro__):
            annotations.update(getattr(base, '__annotations__', {}))
        kind_ann = annotations.get('kind')
        if kind_ann is not None and get_origin(kind_ann) is _Literal:
            args = get_args(kind_ann)
            if args and isinstance(args[0], str):
                PendingInputBase._registry[args[0]] = cls

    pending_id: tuple[int, int]
    kind: str
    instruction: str
    blocking: bool = True

    @property
    def id(self) -> str:
        return f'{self.pending_id[0]}.{self.pending_id[1]}'

    def event_from_form(self, form: Any) -> Any:
        raise NotImplementedError(f'{type(self).__name__}.event_from_form() not implemented')

    def input_specs(self, projection: CharacterProjection) -> list[InputSpec]:
        raise NotImplementedError(f'{type(self).__name__}.input_specs() not implemented')

    def resolve(self, projection: Any, event: Any) -> None:
        pass

    @property
    def template_fragment(self) -> str:
        default = type(self).model_fields['kind'].default
        return default if isinstance(default, str) else 'generic'


def _deserialise_pending_input(v: Any) -> PendingInputBase:
    if isinstance(v, PendingInputBase):
        return v
    if isinstance(v, dict):
        kind = v.get('kind')
        cls = PendingInputBase._registry.get(kind)
        if cls is None:
            raise ValueError(f'Unknown pending input kind: {kind!r}')
        return cls.model_validate(v)
    raise ValueError(f'Cannot deserialise PendingInputBase from {type(v).__name__}')
