"""Shim — domain logic lives in ceres.make.robot.report."""

from ceres.make.robot.report import (
    render_robot_pdf,
    render_robot_spec_pdf,
    render_robot_spec_typst,
    render_robot_typst,
)

__all__ = ['render_robot_pdf', 'render_robot_spec_pdf', 'render_robot_spec_typst', 'render_robot_typst']
