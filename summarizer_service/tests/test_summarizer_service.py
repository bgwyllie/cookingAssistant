import os

import pytest
from fastapi.testclient import TestClient

os.environ["OPENAI_API_KEY"] = "sk-test"

from summarizer_service_app import app

mock_summary = "This One Pot Creamy Mushroom Pasta is a super-rich, umami-filled delight that is, as always, easily prepared in one pot."


class MockChoice:
    def __init__(self):
        self.message = {"content": mock_summary}


class MockResponse:
    def __init__(self):
        self.choices = [MockChoice()]


def mock_create(*args, **kwargs):
    return MockResponse()


@pytest.fixture(autouse=True)
def patch_openai(monkeypatch):
    import openai

    monkeypatch.setattr(openai.ChatCompletion, "create", mock_create)


client = TestClient(app)


def test_summarize_recipe():
    payload = {
        "title": "Creamy mushroom pasta",
        "ingredients": ["pasta", "mushrooms", "cream", "parmesan", "lemon"],
        "steps": [
            "Cook pasta",
            "Chop mushrooms",
            "Cook mushrooms",
            "Add cream and pasta water",
            "Add in pasta",
            "Let reduce",
            "Add lemon zest, salt, and pepper to taste",
        ],
        "tools": ["pot", "pan", "zester"],
        "cook_time_mins": 35,
        "source_url": "http:creamymushroompasta.com",
    }

    res = client.post("/summarize_recipe", json=payload)
    assert res.status_code == 200, res.text

    data = res.json()
    assert "summary" in data
    assert data["summary"] == mock_summary
