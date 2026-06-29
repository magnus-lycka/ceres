"""Unit tests for character/web/app.py — build_app factory."""

from fastapi import FastAPI
import pytest

from ceres.character.app import create_backend
from ceres.character.web.app import build_app


@pytest.fixture
def backend():
    with create_backend(':memory:') as b:
        yield b


class TestBuildApp:
    def test_returns_fastapi_instance(self, backend):
        assert isinstance(build_app(backend), FastAPI)

    def test_app_has_ui_routes(self, backend):
        from fastapi.testclient import TestClient

        client = TestClient(build_app(backend))
        response = client.get('/openapi.json')
        assert response.status_code == 200
        assert any(p.startswith('/ui') for p in response.json()['paths'])

    def test_two_build_app_calls_return_independent_instances(self, backend):
        app1 = build_app(backend)
        app2 = build_app(backend)
        assert app1 is not app2
