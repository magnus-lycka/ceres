from dataclasses import dataclass
from pathlib import Path
from typing import Literal

StuartTheme = Literal['light', 'dark']

_STATIC_DIR = Path(__file__).resolve().parents[2] / 'src' / 'static'


def _light_workbench_bg_url() -> str:
    return (_STATIC_DIR / 'bg_ship_spec_light.jpg').as_uri()


@dataclass(frozen=True)
class ExpanseHtmlPage:
    title: str
    body_html: str
    eyebrow: str | None = None
    extra_head_html: str | None = None
    banner_side_html: str | None = None
    theme: StuartTheme = 'light'


def render_expanse_html_page(page: ExpanseHtmlPage) -> str:
    eyebrow = '' if page.eyebrow is None else f'<p class="eyebrow">{page.eyebrow}</p>'
    extra_head_html = '' if page.extra_head_html is None else page.extra_head_html
    banner_side_html = '' if page.banner_side_html is None else page.banner_side_html
    return f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>{page.title}</title>
    <style>
      :root {{
        --paper: #fffdf5;
        --paper-strong: #f7f1dc;
        --surface: rgba(255, 255, 250, 0.997);
        --surface-strong: rgba(252, 247, 232, 0.997);
        --ink: #0d0d0d;
        --ink-soft: #353126;
        --accent: #cc2036;
        --accent-strong: #e23a4e;
        --warning: #ff7a00;
        --error: #ff1f1f;
        --frame: #1a1a1a;
        --line: rgba(39, 34, 19, 0.48);
        --shadow: rgba(25, 22, 14, 0.08);
        --panel-accent-bg: transparent;
        --page-bg: #633920;
        --page-bg-image: url("{_light_workbench_bg_url()}");
        --shell-bg: #fffdf7;
        --banner-ink: var(--ink);
        --banner-border: var(--line);
        --switch-bg: transparent;
        --switch-bg-hover: rgba(204, 32, 54, 0.1);
        --switch-border: rgba(18, 18, 18, 0.5);
        --switch-ink: var(--ink);
      }}

      body.theme-dark {{
        --paper: #090909;
        --paper-strong: #111112;
        --surface: rgba(20, 20, 21, 0.94);
        --surface-strong: rgba(28, 28, 30, 0.96);
        --ink: #f2f2ee;
        --ink-soft: #cfcac0;
        --accent: #ff3048;
        --accent-strong: #ff5266;
        --warning: #ffbf00;
        --error: #ff3030;
        --frame: #6d6d70;
        --line: rgba(143, 143, 148, 0.34);
        --shadow: rgba(0, 0, 0, 0.44);
        --panel-accent-bg: linear-gradient(180deg, rgba(255, 48, 72, 0.12), rgba(255, 48, 72, 0.04));
        --page-bg: #050505;
        --page-bg-image: none;
        --shell-bg: #101012;
        --banner-ink: var(--ink);
        --banner-border: var(--line);
        --switch-bg: transparent;
        --switch-bg-hover: rgba(255, 48, 72, 0.12);
        --switch-border: rgba(232, 232, 228, 0.3);
        --switch-ink: var(--ink);
      }}

      * {{
        box-sizing: border-box;
      }}

      body {{
        margin: 0;
        font-family: "Avenir Next Condensed", "DIN Condensed", "Arial Narrow", sans-serif;
        color: var(--ink);
        background-color: var(--page-bg);
        background-image: var(--page-bg-image);
        background-position: center top;
        background-repeat: repeat;
        background-size: 960px auto;
        background-attachment: fixed;
      }}

      .page {{
        min-height: 100vh;
        padding: 24px;
      }}

      .shell {{
        max-width: 1100px;
        margin: 0 auto;
        background: var(--shell-bg);
        border: 1px solid var(--frame);
        box-shadow: 0 10px 24px var(--shadow);
        overflow: hidden;
      }}

      .banner {{
        padding: 10px 16px;
        background: transparent;
        color: var(--banner-ink);
        border-bottom: 0;
      }}

      .banner-row {{
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 12px;
      }}

      .banner-main {{
        min-width: 0;
        flex: 1 1 auto;
      }}

      .banner-side {{
        flex: 0 0 auto;
        display: flex;
        align-items: center;
        justify-content: flex-end;
        gap: 8px;
      }}

      .eyebrow {{
        margin: 0 0 2px;
        font-size: 0.72rem;
        letter-spacing: 0.12em;
        text-transform: uppercase;
        color: color-mix(in srgb, var(--banner-ink) 72%, transparent);
      }}

      h1 {{
        margin: 0;
        font-size: clamp(1.4rem, 3.2vw, 2.4rem);
        line-height: 1;
        letter-spacing: 0.03em;
        text-transform: uppercase;
        color: var(--accent);
      }}

      .theme-switch {{
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 2rem;
        height: 2rem;
        padding: 0;
        border: 1px solid var(--switch-border);
        background: var(--switch-bg);
        color: var(--switch-ink);
        font: inherit;
        font-size: 1rem;
        line-height: 1;
        cursor: pointer;
        border-radius: 999px;
      }}

      .theme-switch:hover {{
        background: var(--switch-bg-hover);
        border-color: var(--accent);
      }}

      .content {{
        padding: 16px 18px 20px;
      }}

      @media (max-width: 720px) {{
        .page {{
          padding: 10px;
        }}

        .banner {{
          padding: 10px 12px;
        }}

        .banner-row {{
          flex-direction: column;
          align-items: stretch;
          gap: 8px;
        }}

        .content {{
          padding: 12px 10px 16px;
        }}
      }}

      @media print {{
        :root,
        body.theme-dark {{
          --paper: #fffdf5;
          --paper-strong: #f7f1dc;
          --surface: #fffdfa;
          --surface-strong: #fbf7eb;
          --ink: #0d0d0d;
          --ink-soft: #353126;
          --accent: #cc2036;
          --accent-strong: #e23a4e;
          --warning: #ff7a00;
          --error: #ff1f1f;
          --frame: #1a1a1a;
          --line: rgba(39, 34, 19, 0.48);
          --shadow: transparent;
          --panel-accent-bg: transparent;
          --page-bg: white;
          --page-bg-image: none;
          --shell-bg: #fffdf7;
          --banner-ink: var(--ink);
          --banner-border: var(--line);
          --switch-bg: transparent;
          --switch-bg-hover: transparent;
          --switch-border: rgba(18, 18, 18, 0.5);
          --switch-ink: var(--ink);
        }}

        body {{
          background: white !important;
          color: var(--ink);
        }}

        .shell,
        .banner,
        .banner-meta,
        .spec-table,
        .mini-table,
        .sidebar-card,
        .sidebar-card-title,
        .simple-list,
        .item-notes,
        .item-notes .note-info,
        .item-notes .note-warning,
        .item-notes .note-error,
        .spec-table th,
        .spec-table td,
        .mini-table th,
        .mini-table td {{
          color: #0d0d0d !important;
        }}

        .page {{
          min-height: auto;
          padding: 0;
        }}

        .shell {{
          max-width: none;
          border: 0;
          box-shadow: none;
        }}

        .theme-switch {{
          display: none;
        }}
      }}
    </style>
    {extra_head_html}
  </head>
  <body class="theme-{page.theme}">
    <main class="page">
      <section class="shell">
        <header class="banner">
          <div class="banner-row">
            <div class="banner-main">
              {eyebrow}
              <h1>{page.title}</h1>
            </div>
            <div class="banner-side">
              {banner_side_html}
              <button
                class="theme-switch"
                type="button"
                data-theme-toggle
                aria-label="Switch theme"
                title="Switch theme"
              >◐</button>
            </div>
          </div>
        </header>
        <section class="content">
          {page.body_html}
        </section>
      </section>
    </main>
    <script>
      const body = document.body;
      const themeToggle = document.querySelector('[data-theme-toggle]');

      function setTheme(theme) {{
        body.classList.remove('theme-light', 'theme-dark');
        body.classList.add(`theme-${{theme}}`);
        const nextTheme = theme === 'dark' ? 'light' : 'dark';
        themeToggle.setAttribute('aria-label', `Switch to ${{nextTheme}} theme`);
        themeToggle.setAttribute('title', `Switch to ${{nextTheme}} theme`);
      }}

      if (themeToggle) {{
        setTheme(body.classList.contains('theme-dark') ? 'dark' : 'light');
        themeToggle.addEventListener('click', () => {{
          const nextTheme = body.classList.contains('theme-dark') ? 'light' : 'dark';
          setTheme(nextTheme);
        }});
      }}
    </script>
  </body>
</html>
"""
