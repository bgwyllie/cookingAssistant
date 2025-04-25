import json
import os

import pytest
from fastapi.testclient import TestClient

os.environ["OPENAI_API_KEY"] = "sk-test"

from extractor_service_app import app

mock_recipe = {
    "title": "Creamy Mushroom Pasta",
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


class MockChoice:
    def __init__(self):
        self.message = {
            "role": "function",
            "name": "extract_full_recipe",
            "arguments": json.dumps(mock_recipe),
        }


class MockResponse:
    def __init__(self):
        self.choices = [MockChoice()]


def mock_create(*args, **kwargs):
    return MockResponse()


@pytest.fixture(autouse=True)
def patch_openai(monkeypatch):
    import openai

    monkeypatch.setattr(openai.responses, "create", mock_create)


client = TestClient(app)


def test_extract_recipe_pass():
    payload = {
        "url": "http:creamymushroompasta.com",
        "html": "<html><body>mock</body></html>",
    }
    res = client.post("extract_recipe", json=payload)
    assert res.status_code == 200, res.text

    data = res.json()
    assert data == mock_recipe
