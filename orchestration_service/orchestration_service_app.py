import os
from typing import List

import requests
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

QUERY_PLANNER_URL = os.getenv("QUERY_PLANNER_URL")
SEARCH_SERVICE_URL = os.getenv("SEARCH_SERVICE_URL")
HTML_FETCHER_URL = os.getenv("HTML_FETCHER_URL")
EXTRACTOR_SERVICE_URL = os.getenv("EXTRACTOR_SERVICE_URL")
RANKER_SERVICE_URL = os.getenv("RANKER_SERVICE_URL")

for name, url in [
    ("QUERY_PLANNER_URL", QUERY_PLANNER_URL),
    ("SEARCH_SERVICE_URL", SEARCH_SERVICE_URL),
    ("HTML_FETCHER_URL", HTML_FETCHER_URL),
    ("EXTRACTOR_SERVICE_URL", EXTRACTOR_SERVICE_URL),
    ("RANKER_SERVICE_URL", RANKER_SERVICE_URL),
]:
    if not url:
        raise RuntimeError(f"Missing required environment variable {name}")

app = FastAPI(title="AI Cooking Assistant Orchestration Layer")


class FindRequest(BaseModel):
    ingredients: str
    top_k: int = 3


class RecipeOut(BaseModel):
    title: str
    url: str
    ingredients: List[str]
    steps: List[str]
    tools: List[str]
    cook_time_mins: int
    source_url: str


class FindResponse(BaseModel):
    results: List[RecipeOut]


@app.post("/find_recipes", response_model=FindResponse)
def find_recipes(req: FindRequest):
    # query planning (qp)
    try:
        qp_http_response = requests.post(
            f"{QUERY_PLANNER_URL}/generate_queries",
            json={"ingredients": req.ingredients},
            timeout=90,
        )
        qp_http_response.raise_for_status()
        queries = qp_http_response.json().get("queries", [])
        if not queries:
            raise ValueError("Empty queries list")
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"QueryPlanner error: {e}")

    # web search (ws)
    try:
        ws_http_response = requests.post(
            f"{SEARCH_SERVICE_URL}/search_urls",
            json={"queries": queries, "num_results": req.top_k * 4},
            timeout=60,
        )
        ws_http_response.raise_for_status()
        urls = [item["url"] for item in ws_http_response.json().get("results", [])]
        if not urls:
            raise ValueError("Search returned no URLs")
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"SearchService error: {e}")

    # fetch html (fh)
    html_items = []
    for page_url in urls:
        try:
            fh_http_response = requests.post(
                f"{HTML_FETCHER_URL}/fetch_html", json={"urls": [page_url]}, timeout=60
            )
            fh_http_response.raise_for_status()
            results = fh_http_response.json().get("results", [])
            if results and "html" in results[0]:
                html_items.append(results[0])
        except requests.RequestException as err:
            print(err)
            continue
    if not html_items:
        raise HTTPException(status_code=404, detail="No pages could be fetched")

    # extract recipes (er)
    extracted_recipes = []
    for item in html_items:
        url = item.get("url")
        html = item.get("html")
        if not url or not html:
            continue
        try:
            er_http_response = requests.post(
                f"{EXTRACTOR_SERVICE_URL}/extract_recipe",
                json={"url": url, "html": html},
                timeout=60,
            )
            er_http_response.raise_for_status()
            recipe = er_http_response.json()
            recipe["id"] = recipe["source_url"]
            extracted_recipes.append(recipe)
        except requests.RequestException:
            continue
    if not extracted_recipes:
        raise HTTPException(status_code=404, detail="No recipes extracted")

    # rank recipes (rr)
    try:
        payload = {
            "requirements": {"ingredients": req.ingredients},
            "recipes": extracted_recipes,
            "top_k": req.top_k,
        }
        rr_http_response = requests.post(
            f"{RANKER_SERVICE_URL}/rank_recipes", json=payload, timeout=60
        )
        rr_http_response.raise_for_status()
        top_recipes = rr_http_response.json().get("recipes", [])
        if not top_recipes:
            raise ValueError("Ranker returned no recipes")
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
