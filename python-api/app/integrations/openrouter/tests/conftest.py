import pytest
from fastapi.testclient import TestClient
from main import app  # Asegúrate de importar tu app principal

@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c