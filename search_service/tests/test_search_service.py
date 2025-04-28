import os

import pytest
from fastapi.testclient import TestClient

os.environ["OPENAI_API_KEY"] = "sk-test"

from search_service_app import app

mock_choice = {
    "output": [
        {
            "type": "web_search_call",
            "results": [
                {
                    "title": "title 1",
                    "url": "http://recipe1.com",
                },
                {
                    "title": "title 2",
                    "url": "http://recipe2.com",
                },
                {
                    "title": "title 3",
                    "url": "http://recipe3.com",
                },
            ],
        }
    ]
}


@pytest.fixture(autouse=True)
def patch_openai(monkeypatch):
    import openai

    monkeypatch.setattr(openai.responses, "create", lambda *args, **kw: mock_choice)


client = TestClient(app)


def test_search_urls_gpt_preview():
    payload = {"queries": ["test query"], "num_results": 2}
    res = client.post("/search_urls", json=payload)
    assert res.status_code == 200, res.text
    data = res.json()
    assert data["results"] == [
        {
            "title": "title 1",
            "url": "http://recipe1.com",
        },
        {
            "title": "title 2",
            "url": "http://recipe2.com",
        },
    ]
