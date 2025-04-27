import os
import time

import requests

BASE = "http://localhost:8000"


def test_find_recipes_e2e():
    time.sleep(5)
    payload = {"ingredients": ["mushrooms", "cream"], "top_k": 3}
    http_response = requests.post(f"{BASE}/find_recipes", json=payload, timeout=30)
    assert http_response.status_code == 200, http_response.text
    data = http_response.json()
    assert "results" in data and len(data["results"]) <= 2
    for recipe in data["results"]:
        assert "title" in recipe and "url" in recipe
