"""Grades: the words the Vehicle Handbook grades its options by.

The same six words name the steps of its Tech Level Stages table, and grade
control systems, autopilots, sensors, collision protection, power plants and
transceivers. Each option allows only the grades its own table lists.

Rules: refs/vehicle/08_options.md, refs/vehicle/09_core_options.md
"""

from enum import StrEnum


class Grade(StrEnum):
    PRIMITIVE = 'primitive'
    BASIC = 'basic'
    IMPROVED = 'improved'
    ENHANCED = 'enhanced'
    ADVANCED = 'advanced'
    SUPERIOR = 'superior'
