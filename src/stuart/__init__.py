"""Stuart is the presentation and rendering layer for Ceres-adjacent tools.

The first target is HTML output, with an Expanse-inspired theme.
Unlike `tycho`, this package is intentionally not specific to ship-design
models. It should be able to render other structured outputs later on.
"""

from .html import ExpanseHtmlPage, StuartTheme, render_expanse_html_page
from .tycho_html import render_ship_html, render_ship_spec_html

__all__ = ['ExpanseHtmlPage', 'StuartTheme', 'render_expanse_html_page', 'render_ship_html', 'render_ship_spec_html']
