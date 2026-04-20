"""Stuart is the presentation and rendering layer for Ceres-adjacent tools.

The first target is HTML output, with an Expanse-inspired theme.
Unlike `tycho`, this package is intentionally not specific to ship-design
models. It should be able to render other structured outputs later on.
"""

from .html import ExpanseHtmlPage, StuartTheme, copy_static_assets, render_expanse_html_page
from .tycho_html import render_ship_html, render_ship_spec_html
from .tycho_pdf import render_ship_pdf, render_ship_spec_pdf, render_ship_spec_typst, render_ship_typst

__all__ = [
    'ExpanseHtmlPage',
    'StuartTheme',
    'copy_static_assets',
    'render_expanse_html_page',
    'render_ship_html',
    'render_ship_spec_html',
    'render_ship_pdf',
    'render_ship_spec_pdf',
    'render_ship_spec_typst',
    'render_ship_typst',
]
