import json
import os

import pytest
from fastapi.testclient import TestClient

os.environ["OPENAI_API_KEY"] = "sk-test"

from search_service_app import app


class MockChoice:
    def __init__(self, content):
        self.message = {
            "role": "function",
            "name": "browser.search",
            "content": json.dumps(
                {
                    "results": [
                        {
                            "title": "title 1",
                            "url": "http://recipe1.com",
                            "recipe_description": "recipe 1 description",
                        },
                        {
                            "title": "title 2",
                            "url": "http://recipe2.com",
                            "recipe_description": "recipe 2 description",
                        },
                        {
                            "title": "title 3",
                            "url": "http://recipe3.com",
                            "recipe_description": "recipe 3 description",
                        },
                    ]
                }
            ),
        }


class MockResponse:
    def __init__(self):
        self.choices = [MockChoice(None)]


def mock_create(*args, **kwargs):
    return MockResponse()


@pytest.fixture(autouse=True)
def patch_openai(monkeypatch):
    import openai

    monkeypatch.setattr(openai.ChatCompletion, "create", mock_create)


client = TestClient(app)


def test_search_urls_gpt_preview():
    payload = {"queries": ["test query"], "num_results": 2}
    res = client.post("/search_urls", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "results" in data
    assert len(data["results"]) == 2
    urls = {item["url"] for item in data["results"]}
    assert urls == {"http://recipe1.com", "http://recipe2.com"}
