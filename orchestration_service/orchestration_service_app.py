import os
from typing import List

import requests
from config import settings
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# load_dotenv(os.path.join(os.path.dirname(__file__), "../.env"))
load_dotenv("../.env")

QUERY_PLANNER_URL = os.getenv("QUERY_PLANNER_URL", "http://query_planner:8001")
SEARCH_SERVICE_URL = os.getenv("SEARCH_SERVICE_URL", "http://search_service:8002")
HTML_FETCHER_URL = os.getenv("HTML_FETCHER_URL", "http://html_fetcher:8002")
EXTRACTOR_SERVICE_URL = os.getenv(
    "EXTRACTOR_SERVICE_URL", "http://extractor_service:8002"
)
RANKER_SERVICE_URL = os.getenv("RANKER_SERVICE_URL", "http://ranker_service:8002")
SUMMARIZER_SERVICE_URL = os.getenv(
    "SUMMARIZER_SERVICE_URL", "http://summarizer_service:8002"
)

app = FastAPI(title="AI Cooking Assistant Orchestration layer")


class FindRequest(BaseModel):
    ingredients: List[str]
    top_k: int = 5


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
            timeout=5,
        )
        http_response.raise_for_status()
        queries = http_response.json()["queries"]
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"QueryPlanner error: {e}")

    # web search
    try:
        http_response = requests.post(
            f"{settings.SEARCH_URL}/search_urls",
            json={"queries": queries, "num_results": req.top_k * 4},
            timeout=5,
        )
        http_response.raise_for_status()
        urls = [i["url"] for i in http_response.json()["results"]]
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"SearchService error: {e}")

    # fetch html
    try:
        http_response = requests.post(
            f"{settings.HTML_URL}/fetch_url", json={"urls": urls}, timeout=10
        )
        http_response.raise_for_status()
        html_items = http_response.json()["results"]
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"HTMLFetcher error: {e}")

    # extract recipes
    extracted_recipes = []
    for item in html_items:
        try:
            http_response = requests.post(
                f"{settings.EXTRACT_URL}/extract_recipe",
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
            f"{settings.RANK_URL}/rank_recipes", json=payload, timeout=5
        )
        http_response.raise_for_status()
        top_recipes = http_response.json()["recipes"]
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"RankService error: {e}")

    # summary service
    results = []
    for recipe in top_recipes:
        try:
            http_response = requests.post(
                f"{settings.SUMMARY_URL}/summarize_recipe", json=recipe, timeout=5
            )
            http_response.raise_for_status()
            summary = http_response.json().get("summary", "")
        except:
            summary = ""
        full_recipe = {
            "title": recipe["title"],
            "url": recipe["source_url"],
            "summary": summary,
            "ingredients": recipe["ingredients"],
            "steps": recipe["steps"],
            "tools": recipe["tools"],
            "cook_time_mins": recipe["cook_time_mins"],
            "source_url": recipe["source_url"],
        }
        results.append(full_recipe)

    return FindResponse(results=results)
