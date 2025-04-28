import os

import pytest
from fastapi.testclient import TestClient

os.environ["OPENAI_API_KEY"] = "sk-test"

from query_planner_app import app

mock_content = "mushroom risotto\ncreamy mushroom pasta"


class MockChoice:
    def __init__(self, content):
        self.message = {"content": content}


class MockResponse:
    def __init__(self, content):
        self.choices = [MockChoice(content)]


def mock_create(*args, **kwargs):
    return {"output": [{"content": [{"text": mock_content}]}]}


@pytest.fixture(autouse=True)
def patch_openai(monkeypatch):
    import openai

    monkeypatch.setattr(openai.responses, "create", mock_create)


client = TestClient(app)


def test_generate_queries():
    payload = {"ingredients": "mushroom cream"}
    res = client.post("/generate_queries", json=payload)
    assert res.status_code == 200, res.text

    data = res.json()
    assert "queries" in data
    assert isinstance(data["queries"], list)

    assert data["queries"] == ["mushroom risotto", "creamy mushroom pasta"]
