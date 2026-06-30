"""Unit tests for character/web/app.py — build_app factory."""

from fastapi import FastAPI

from ceres.character.service import CharacterService
from ceres.character.web.app import build_app


class TestBuildApp:
    def test_returns_fastapi_instance(self):
        with CharacterService(':memory:') as service:
            assert isinstance(build_app(service), FastAPI)

    def test_app_has_ui_routes(self):
        from fastapi.testclient import TestClient

        with CharacterService(':memory:') as service:
            client = TestClient(build_app(service))
            response = client.get('/openapi.json')
            assert response.status_code == 200
            assert any(p.startswith('/ui') for p in response.json()['paths'])

    def test_two_build_app_calls_return_independent_instances(self):
        with CharacterService(':memory:') as service:
            app1 = build_app(service)
            app2 = build_app(service)
            assert app1 is not app2
