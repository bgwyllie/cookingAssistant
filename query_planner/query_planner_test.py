import json
import os

import pytest
from fastapi.testclient import TestClient

os.environ["OPENAI_API_KEY"] = "sk-test"

from query_planner_app import app

client = TestClient(app)


class DummyChoice:
    def __init__(self, content):
        self.message = {"content": content}


def dummy_chatcompletion_create(*args, **kwargs):
    return {"choices": [DummyChoice("mushroom risotto\n creamy mushroom pasta")]}


@pytest.fixture(autouse=True)
def patch_openai(patch):
    import openai

    patch.setattr(openai.ChatCompletion, "create", dummy_chatcompletion_create)


def test_generate_queries():
    payload = {"ingredients": ["mushroom", "cream"]}
    res = client.post("/generate_queries", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "queries" in data
    assert isinstance(data["queries"], list)
    assert data["queries"][0].startswith("mushroom risotto")
