import json
import os

import pytest
from fastapi.testclient import TestClient

os.environ["QUERY_URL"] = "http://mockqueryurl"
os.environ["SEARCH_URL"] = "http://mocksearchurl"
os.environ["HTML_URL"] = "http://mockhtmlurl"
os.environ["EXTRACT_URL"] = "http://mockextracturl"
os.environ["RANK_URL"] = "http://mockrankurl"
os.environ["SUMMARY_URL"] = "http://mocksummaryurl"

from orchestration_service_app import app

client = TestClient(app)


class MockResponse:
    def __init__(self, data):
        self._data = data

    def raise_for_status(self):
        pass

    def json(self):
        return self._data


@pytest.fixture(autouse=True)
def patch_request(monkeypatch):
    import requests

    mock_response_objects = []

    # generate queries
    mock_response_objects.append(MockResponse({"queries": ["query1", "query2"]}))
    # search urls
    mock_response_objects.append(
        MockResponse({"results": [{"url": "url1"}, {"url": "url2"}, {"url": "url3"}]})
    )
    # fetch html
    mock_response_objects.append(
        MockResponse(
            {
                "results": [
                    {"url": "url1", "html": "<html>html1</html>"},
                    {"url": "url2", "html": "<html>html2</html>"},
                    {"url": "url3", "html": "<html>html3</html>"},
                ]
            }
        )
    )
    # extract recipe
    recipe1 = {
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
    recipe2 = {
        "title": "Mushroom risotto",
        "ingredients": [
            "arborio rice",
            "mushrooms",
            "white wine",
            "parmesan",
            "vegetable broth",
            "onion",
            "garlic",
        ],
        "steps": [
            "Chop mushrooms, onion and garlic",
            "Cook onion and garlic until fragrant",
            "Add mushrooms",
            "Add in rice",
            "Slowly add in wine and broth",
            "Add salt, and pepper to taste",
        ],
        "tools": ["pot", "pan", "laddle"],
        "cook_time_mins": 45,
        "source_url": "http:mushroomrisotto.com",
    }
    recipe3 = {
        "title": "Cream of mushroom soup",
        "ingredients": [
            "mushrooms",
            "dried thyme",
            "butter",
            "vegetable broth",
            "onion",
            "flour",
            "sherry",
        ],
        "steps": [
            "Simmer mushrooms, stock, onion, and thyme until vegetables are tender",
            "Blend in a food processor",
            "Melt butter and whisk in flour in pan",
            "Add in mushroom mixture",
            "Bring to a boil",
            "Add in sherry, salt, and pepper to taste",
        ],
        "tools": ["large saucepan", "food processor", "whisk"],
        "cook_time_mins": 50,
        "source_url": "http:creamofmushroomsoup.com",
    }
    mock_response_objects.append(MockResponse(recipe1))
    mock_response_objects.append(MockResponse(recipe2))
    mock_response_objects.append(MockResponse(recipe3))
    # rank recipes
    mock_response_objects.append(MockResponse({"recipes": [recipe3, recipe1, recipe2]}))
    # summarize recipe
    mock_response_objects.append(
        MockResponse(
            {
                "summary": "This mushroom soup recipe is creamy, comforting, and bursting with savory mushroom flavor."
            }
        )
    )
    mock_response_objects.append(
        MockResponse(
            {
                "summary": "This One Pot Creamy Mushroom Pasta is a super-rich, umami-filled delight that is, as always, easily prepared in one pot."
            }
        )
    )
    mock_response_objects.append(
        MockResponse(
            {
                "summary": "Creamy, comforting, and packed with rich umami flavors, this mushroom risotto recipe is the perfect comfort food for any occasion"
            }
        )
    )

    def fake_post(url, json, timeout):
        return mock_response_objects.pop(0)

    monkeypatch.setattr(requests, "post", fake_post)


def test_find_recipes():
    requirements = {"ingredients": ["mushrooms", "cream"], "top_k": 3}

    response_recipe = client.post("/find_recipes", json=requirements)
    print("QWERTY", response_recipe)
    assert response_recipe.status_code == 200

    recipes = response_recipe.json()
    assert len(recipes["results"]) == 3
    assert recipes["results"][0]["title"] == "Cream of mushroom soup"
    assert (
        recipes["results"][0]["summary"]
        == "This mushroom soup recipe is creamy, comforting, and bursting with savory mushroom flavor."
    )
    assert recipes["results"][1]["title"] == "Creamy mushroom pasta"
    assert (
        recipes["results"][1]["summary"]
        == "This One Pot Creamy Mushroom Pasta is a super-rich, umami-filled delight that is, as always, easily prepared in one pot."
    )
    assert recipes["results"][2]["title"] == "Mushroom risotto"
    assert (
        recipes["results"][2]["summary"]
        == "Creamy, comforting, and packed with rich umami flavors, this mushroom risotto recipe is the perfect comfort food for any occasion"
    )
