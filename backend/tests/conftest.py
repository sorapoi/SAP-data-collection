import pytest
from fastapi.testclient import TestClient
from ..main import app

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def test_user():
    return {
        "username": "test_user",
        "password": "test_password",
        "department": "信息部"
    } 