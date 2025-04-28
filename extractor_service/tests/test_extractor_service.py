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

mock_response = {
    "output": [
        {
            "type": "message",
            "content": [{"type": "output_text", "text": json.dumps(mock_recipe)}],
        }
    ]
}


class MockResponse:
    def __init__(self, text):
        self.output_text = text


@pytest.fixture(autouse=True)
def patch_openai(monkeypatch):
    import openai

    json_text = json.dumps(mock_recipe)
    monkeypatch.setattr(
        openai.responses, "create", lambda *args, **kwargs: MockResponse(json_text)
    )


client = TestClient(app)


def test_extract_recipe_pass():
    payload = {
        "url": "http:creamymushroompasta.com",
        "html": "<html><body>mock</body></html>",
    }
    recipe_response = client.post("/extract_recipe", json=payload)
    assert recipe_response.status_code == 200, recipe_response.text

    data = recipe_response.json()
    assert data == mock_recipe
