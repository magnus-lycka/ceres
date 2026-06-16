from typing import Annotated, Any, ClassVar, Literal, get_args, get_origin

from pydantic import BaseModel, BeforeValidator, SerializeAsAny


class EventHandlerBase(BaseModel):
    _registry: ClassVar[dict[str, type[EventHandlerBase]]] = {}

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        # model_fields is not yet populated at __init_subclass__ time in Pydantic V2,
        # so we inspect __annotations__ directly for the Literal 'kind' field.
        annotations: dict[str, Any] = {}
        for base in reversed(cls.__mro__):
            annotations.update(getattr(base, '__annotations__', {}))
        kind_ann = annotations.get('kind')
        if kind_ann is not None and get_origin(kind_ann) is Literal:
            args = get_args(kind_ann)
            if args and isinstance(args[0], str):
                EventHandlerBase._registry[args[0]] = cls

    def apply(self, projection: Any, event: Event, fulfilled_pending: Any = None) -> None:
        raise NotImplementedError(f'{type(self).__name__}.apply() not implemented')

    def init_replay(self, character_id: int, event_id: int) -> Any:
        return None


def _deserialise_event_handler(v: Any) -> EventHandlerBase:
    if isinstance(v, EventHandlerBase):
        return v
    if isinstance(v, dict):
        kind = v.get('kind')
        cls = EventHandlerBase._registry.get(kind)
        if cls is None:
            raise ValueError(f'Unknown event handler kind: {kind!r}')
        return cls.model_validate(v)
    raise ValueError(f'Cannot deserialise EventHandlerBase from {type(v).__name__}')


class Event(BaseModel):
    id: int = 0
    fulfills: tuple[int, int] | str | None = None
    handler: Annotated[SerializeAsAny[EventHandlerBase], BeforeValidator(_deserialise_event_handler)]

    @property
    def kind(self) -> str:
        return getattr(self.handler, 'kind', '')

    def apply(self, projection: Any, fulfilled_pending: Any = None) -> None:
        self.handler.apply(projection, self, fulfilled_pending)

    def __getattr__(self, name: str) -> Any:
        """Proxy attribute access to handler for backward compatibility with resolve() methods."""
        # Only proxy if the attribute is not found on Event itself
        try:
            handler = object.__getattribute__(self, 'handler')
            return getattr(handler, name)
        except AttributeError:
            raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'") from None


class PendingHandlerBase(BaseModel):
    _registry: ClassVar[dict[str, type[PendingHandlerBase]]] = {}

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        annotations: dict[str, Any] = {}
        for base in reversed(cls.__mro__):
            annotations.update(getattr(base, '__annotations__', {}))
        kind_ann = annotations.get('kind')
        if kind_ann is not None and get_origin(kind_ann) is Literal:
            args = get_args(kind_ann)
            if args and isinstance(args[0], str):
                PendingHandlerBase._registry[args[0]] = cls

    def resolve(self, projection: Any, event: Event) -> None:
        pass

    def input_specs(self) -> list:
        return []

    def event_from_form(self, form: Any, pending_id: tuple[int, int]) -> Event:
        raise NotImplementedError(f'{type(self).__name__}.event_from_form() not implemented')


def _deserialise_pending_handler(v: Any) -> PendingHandlerBase:
    if isinstance(v, PendingHandlerBase):
        return v
    if isinstance(v, dict):
        kind = v.get('kind')
        cls = PendingHandlerBase._registry.get(kind)
        if cls is None:
            raise ValueError(f'Unknown pending handler kind: {kind!r}')
        return cls.model_validate(v)
    raise ValueError(f'Cannot deserialise PendingHandlerBase from {type(v).__name__}')


class PendingInput(BaseModel):
    pending_id: tuple[int, int]
    blocking: bool = True
    handler: Annotated[PendingHandlerBase, BeforeValidator(_deserialise_pending_handler)]

    @property
    def id(self) -> str:
        return f'{self.pending_id[0]}.{self.pending_id[1]}'
