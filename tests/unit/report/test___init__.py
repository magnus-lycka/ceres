from ceres.report import render_html, render_pdf, render_pdf_source, render_typst_source


def test_low_level_render_functions_are_callable():
    assert callable(render_html)
    assert callable(render_typst_source)
    assert callable(render_pdf_source)
    assert callable(render_pdf)
