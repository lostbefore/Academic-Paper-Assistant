"""Pytest fixtures: isolated data directory and an app instance per session."""

from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
BACKEND = REPO_ROOT / "backend"
sys.path.insert(0, str(BACKEND))

# Configure before importing the app: the settings object is created at import
# time and caches the data directory.
_TMP = tempfile.mkdtemp(prefix="apa-test-")
os.environ.update(
    {
        "DATA_DIR": _TMP,
        "JWT_SECRET": "test-secret-key-for-pytest-only",
        "LLM_API_KEY": "test-placeholder-key",
        "LLM_PROVIDER": "openai",
        "LLM_BASE_URL": "http://127.0.0.1:9/v1",  # deliberately unreachable
        "ADMIN_EMAIL": "admin@test.local",
        "ADMIN_PASSWORD": "TestPassw0rd!",
        "ADMIN_NAME": "Test Admin",
        "ALLOW_REGISTRATION": "true",
        "APP_ENV": "test",
        "MAX_CONCURRENT_JOBS": "1",
    }
)

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402


@pytest.fixture(scope="session")
def client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(scope="session")
def admin_token(client):
    response = client.post(
        "/api/auth/login", json={"email": "admin@test.local", "password": "TestPassw0rd!"}
    )
    assert response.status_code == 200, response.text
    return response.json()["access_token"]


@pytest.fixture(scope="session")
def auth_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}"}
