import json
import os

import pytest
from fastapi.testclient import TestClient

os.environ["OPENAI_API_KEY"] = "sk-test"

from ranker_service_app import Recipe, app

mock_recipes = [
    Recipe(
        id="recipe1",
        title="Creamy mushroom pasta",
        ingredients=["pasta", "mushrooms", "cream", "parmesan", "lemon"],
        steps=[
            "Cook pasta",
            "Chop mushrooms",
            "Cook mushrooms",
            "Add cream and pasta water",
            "Add in pasta",
            "Let reduce",
            "Add lemon zest, salt, and pepper to taste",
        ],
        tools=["pot", "pan", "zester"],
        cook_time_mins=35,
        source_url="http://creamymushroompasta.com",
    ),
    Recipe(
        id="recipe2",
        title="Mushroom risotto",
        ingredients=[
            "arborio rice",
            "mushrooms",
            "white wine",
            "parmesan",
            "vegetable broth",
            "onion",
            "garlic",
        ],
        steps=[
            "Chop mushrooms, onion and garlic",
            "Cook onion and garlic until fragrant",
            "Add mushrooms",
            "Add in rice",
            "Slowly add in wine and broth",
            "Add salt, and pepper to taste",
        ],
        tools=["pot", "pan", "laddle"],
        cook_time_mins=45,
        source_url="http://mushroomrisotto.com",
    ),
    Recipe(
        id="recipe3",
        title="Cream of mushroom soup",
        ingredients=[
            "mushrooms",
            "dried thyme",
            "butter",
            "vegetable broth",
            "onion",
            "flour",
            "sherry",
        ],
        steps=[
            "Simmer mushrooms, stock, onion, and thyme until vegetables are tender",
            "Blend in a food processor",
            "Melt butter and whisk in flour in pan",
            "Add in mushroom mixture",
            "Bring to a boil",
            "Add in sherry, salt, and pepper to taste",
        ],
        tools=["large saucepan", "food processor", "whisk"],
        cook_time_mins=50,
        source_url="http://creamofmushroomsoup.com",
    ),
]

LLM_Rank = {"ranked_ids": ["recipe3", "recipe1", "recipe2"]}


class MockResponse:
    def __init__(self):
        self.output_text = json.dumps(LLM_Rank)


@pytest.fixture(autouse=True)
def patch_openai(monkeypatch):
    import openai

    monkeypatch.setattr(
        openai.responses, "create", lambda *args, **kwargs: MockResponse()
    )


client = TestClient(app)


def test_rank_recipes_default_top_k():
    payload = {
        "requirements": {"ingredients": "mushrooms cream"},
        "recipes": [r.model_dump() for r in mock_recipes],
    }
    res = client.post("/rank_recipes", json=payload)
    assert res.status_code == 200, res.text

    out = res.json()
    assert [r["id"] for r in out["recipes"]] == ["recipe3", "recipe1", "recipe2"]


def test_rank_recipes_custom_top_k():
    payload = {
        "requirements": {"ingredients": "mushrooms cream"},
        "recipes": [r.model_dump() for r in mock_recipes],
        "top_k": 2,
    }
    res = client.post("/rank_recipes", json=payload)
    assert res.status_code == 200, res.text

    out = res.json()
    assert [r["id"] for r in out["recipes"]] == ["recipe3", "recipe1"]
