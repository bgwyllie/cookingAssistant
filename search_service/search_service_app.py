import os
from typing import List

import openai
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

openai.api_key = os.getenv("OPENAI_API_KEY")
if not openai.api_key:
    raise RuntimeError("missing open ai key")


class SearchRequest(BaseModel):
    queries: List[str]
    num_results: int = 10


class SearchResult(BaseModel):
    title: str
    url: str


class SearchResponse(BaseModel):
    results: List[SearchResult]


app = FastAPI(title="Search Service")


@app.post("/search_urls", response_model=SearchResponse)
def search_urls(req: SearchRequest):
    seen_recipes = set()
    results: List[SearchResult] = []

    for q in req.queries:
        try:
            response = openai.responses.create(
                model="gpt-4.1-mini",
                instructions="You are a web search assistant",
                input=q,
                tools=[
                    {
                        "type": "web_search_preview",
                    }
                ],
                tool_choice="required",
                include=["web_search_call.results"],
                temperature=0,
            )
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"Search-plugin error: {e}")

        data = response.to_dict() if hasattr(response, "to_dict") else dict(response)
        output = data.get("output", [])
        for item in output:
            if item.get("type") == "web_search_call" and "results" in item:
                hits = item["results"]
                break
        else:
            hits = []
            for item in output:
                if item.get("type") == "message":
                    for chunk in item.get("content", []):
                        for annotation in chunk.get("annotations", []):
                            hits.append(
                                {"title": annotation["title"], "url": annotation["url"]}
                            )
                    if hits:
                        break

        for hit in hits:
            url = hit.get("url")
            if not url or url in seen_recipes:
                continue
            seen_recipes.add(url)
            results.append(
                SearchResult(
                    title=hit.get("title", ""),
                    url=url,
                )
            )

        if len(results) >= req.num_results:
            break

    return SearchResponse(results=results[: req.num_results])
