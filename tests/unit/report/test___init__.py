from ceres.report import (
    render_html,
    render_pdf,
    render_pdf_source,
    render_robot_pdf,
    render_robot_spec_pdf,
    render_robot_spec_typst,
    render_robot_typst,
    render_ship_html,
    render_ship_pdf,
    render_ship_spec_html,
    render_ship_spec_pdf,
    render_ship_spec_typst,
    render_ship_typst,
    render_typst_source,
)


def test_ship_render_functions_are_callable():
    assert callable(render_ship_html)
    assert callable(render_ship_typst)
    assert callable(render_ship_pdf)
    assert callable(render_ship_spec_html)
    assert callable(render_ship_spec_typst)
    assert callable(render_ship_spec_pdf)


def test_robot_render_functions_are_callable():
    assert callable(render_robot_typst)
    assert callable(render_robot_pdf)
    assert callable(render_robot_spec_typst)
    assert callable(render_robot_spec_pdf)


def test_low_level_render_functions_are_callable():
    assert callable(render_html)
    assert callable(render_typst_source)
    assert callable(render_pdf_source)
    assert callable(render_pdf)
