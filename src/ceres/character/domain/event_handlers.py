"""Registration bootstrap for event handlers persisted in character logs."""

from functools import cache
import importlib

from ceres.character.domain.career.loader import load_careers

_EVENT_HANDLER_MODULES = (
    'ceres.character.domain.character_start',
    'ceres.character.domain.choice_events',
    'ceres.character.domain.connection_events',
    'ceres.character.domain.health.health_events',
    'ceres.character.domain.homeworld.homeworld_events',
    'ceres.character.domain.life_events',
    'ceres.character.domain.precareer.precareer_events',
    'ceres.character.domain.psionics',
    'ceres.character.domain.skill_events',
    'ceres.character.domain.career.advancement',
    'ceres.character.domain.career.career_events',
    'ceres.character.domain.career.entry',
    'ceres.character.domain.career.muster_out',
    'ceres.character.domain.career.prisoner_events',
)


@cache
def register_event_handlers() -> None:
    """Import every module that owns a handler which may appear in an event log."""
    for module_name in _EVENT_HANDLER_MODULES:
        importlib.import_module(module_name)
    load_careers()
