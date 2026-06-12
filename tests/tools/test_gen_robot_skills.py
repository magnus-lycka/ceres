"""Tests for the robot skill facade generator.

The generator produces Python source. These tests exec that source and verify
the resulting classes behave correctly — not that the source looks a particular way.
"""

from tools.gen_robot_skills import generate_module


def _exec_module(src: str) -> dict:
    """Exec generated source in an isolated namespace and return it."""
    ns: dict = {}
    exec(compile(src, '<generated>', 'exec'), ns)
    return ns


def test_generated_module_compiles():
    compile(generate_module(), '<generated>', 'exec')


def test_admin_is_importable_and_has_level_zero_default():
    ns = _exec_module(generate_module())
    Admin = ns['Admin']
    assert Admin().level == 0


def test_electronics_fields_default_to_zero():
    ns = _exec_module(generate_module())
    Electronics = ns['Electronics']
    pkg = Electronics()
    assert pkg.comms == 0
    assert pkg.computers == 0
    assert pkg.sensors == 0
    assert pkg.remote_ops == 0


def test_electronics_accepts_int_fields():
    ns = _exec_module(generate_module())
    Electronics = ns['Electronics']
    pkg = Electronics(comms=1, computers=2)
    assert pkg.comms == 1
    assert pkg.computers == 2


def test_robot_profession_is_present():
    ns = _exec_module(generate_module())
    assert 'RobotProfession' in ns
