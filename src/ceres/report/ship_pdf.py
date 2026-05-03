"""Shim — domain logic lives in ceres.make.ship.report."""

from ceres.make.ship.report import (
    render_ship_pdf,
    render_ship_spec_pdf,
    render_ship_spec_typst,
    render_ship_typst,
)

__all__ = ['render_ship_pdf', 'render_ship_spec_pdf', 'render_ship_spec_typst', 'render_ship_typst']
