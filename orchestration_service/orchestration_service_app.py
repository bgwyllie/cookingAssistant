import os
from typing import List

import requests
from config import settings
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

QUERY_PLANNER_URL = os.getenv("QUERY_PLANNER_URL", "http://query_planner:8001")
SEARCH_SERVICE_URL = os.getenv("SEARCH_SERVICE_URL", "http://search_service:8002")
HTML_FETCHER_URL = os.getenv("HTML_FETCHER_URL", "http://html_fetcher:8003")
EXTRACTOR_SERVICE_URL = os.getenv(
    "EXTRACTOR_SERVICE_URL", "http://extractor_service:8004"
)
RANKER_SERVICE_URL = os.getenv("RANKER_SERVICE_URL", "http://ranker_service:8005")

app = FastAPI(title="AI Cooking Assistant Orchestration layer")


class FindRequest(BaseModel):
    ingredients: List[str]
    top_k: int = 3


class RecipeOut(BaseModel):
    title: str
    url: str
    summary: str
    ingredients: List[str]
    steps: List[str]
    tools: List[str]
    cook_time_mins: int
    source_url: str


class FindResponse(BaseModel):
    results: List[RecipeOut]


@app.post("/find_recipes", response_model=FindResponse)
def find_recipes(req: FindRequest):
    # query planning
    try:
        http_response = requests.post(
            f"{QUERY_PLANNER_URL}/generate_queries",
            json={"ingredients": req.ingredients},
            timeout=(3, 30),
        )
        http_response.raise_for_status()
        queries = http_response.json().get("queries", [])
    except requests.Timeout:
        raise HTTPException(status_code=504, detail=f"QueryPlanner timed out")
    except requests.RequestException as e:
        raise HTTPException(status_code=502, detail=f"QueryPlanner error: {e}")

    # web search
    try:
        http_response = requests.post(
            f"{SEARCH_SERVICE_URL}/search_urls",
            json={"queries": queries, "num_results": req.top_k * 4},
            timeout=60,
        )
        http_response.raise_for_status()
        urls = [i["url"] for i in http_response.json().get("results", [])]
    except requests.Timeout:
        raise HTTPException(status_code=504, detail=f"SearchService timed out")
    except requests.RequestException as e:
        raise HTTPException(status_code=502, detail=f"SearchService error: {e}")

    # fetch html
    try:
        http_response = requests.post(
            f"{HTML_FETCHER_URL}/fetch_html", json={"urls": urls}, timeout=60
        )
        http_response.raise_for_status()
        html_items = http_response.json().get("results", [])
    except requests.Timeout:
        raise HTTPException(status_code=504, detail=f"HTMLFetcher timed out")
    except requests.RequestException as e:
        raise HTTPException(status_code=502, detail=f"HTMLFetcher error: {e}")

    # extract recipes
    extracted_recipes = []
    for item in html_items:
        try:
            http_response = requests.post(
                f"{EXTRACTOR_SERVICE_URL}/extract_recipe",
                json={"url": item["url"], "html": item["html"]},
                timeout=10,
            )
            http_response.raise_for_status()
            extracted_recipes.append(http_response.json())
        except:
            continue
    if not extracted_recipes:
        raise HTTPException(status_code=404, detail="No recipes extracted")

    # rank recipes
    try:
        payload = {
            "requirements": {"ingredients": req.ingredients},
            "recipes": extracted_recipes,
            "top_k": req.top_k,
        }
        http_response = requests.post(
            f"{RANKER_SERVICE_URL}/rank_recipes", json=payload, timeout=5
        )
        http_response.raise_for_status()
        top_recipes = http_response.json()["recipes"]
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"RankService error: {e}")

    # full response
    output_recipe = []
    for recipe in top_recipes:
        output_recipe.append(
            {
                "title": recipe["title"],
                "url": recipe["source_url"],
                "ingredients": recipe["ingredients"],
                "steps": recipe["steps"],
                "tools": recipe["tools"],
                "cook_time_mins": recipe["cook_time_mins"],
                "source_url": recipe["source_url"],
            }
        )

    return FindResponse(results=output_recipe)
