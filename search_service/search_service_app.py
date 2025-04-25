import json
import os
from typing import List, Optional

import openai
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

load_dotenv(os.path.join(os.path.dirname(__file__), "../.env"))

openai.api_key = os.getenv("OPENAI_API_KEY")
if not openai.api_key:
    raise RuntimeError("missing open ai key")


class SearchRequest(BaseModel):
    queries: List[str]
    num_results: Optional[int] = 10


class SearchResult(BaseModel):
    title: str
    url: str
    recipe_description: Optional[str] = None


class SearchResponse(BaseModel):
    results: List[SearchResult]


browser_search_schema = {
    "name": "browser.search",
    "description": "Search the web for recipes using the browser plugin",
    "parameters": {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "Search terms"},
            "num_results": {
                "type": "integer",
                "description": "Max number of results to return",
            },
        },
        "required": ["query"],
    },
}

app = FastAPI(title="Search Service (GPT 4o Web Search Preview)")


@app.post("/search_urls", response_model=SearchResponse)
def search_urls(req: SearchRequest):
    seen = set()
    out: List[SearchResult] = []

    for q in req.queries:
        try:
            res = openai.responses.create(
                model="gpt-4o-web-preview",
                instructions="You are a web search assistant",
                input=q,
                tools=[browser_search_schema],
                tool_choice="browser.search",
            )
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"Search-plugin error: {e}")

        response_message = res.choices[0].message
        if (
            response_message.get("role") == "function"
            and response_message.get("name") == "browser.search"
        ):
            try:
                data = json.loads(response_message["content"])
            except json.JSONDecodeError:
                continue
            for item in data.get("results", []):
                url = item.get("url")
                if not url or url in seen:
                    continue
                seen.add(url)
                out.append(
                    SearchResult(
                        title=item.get("title", ""),
                        url=url,
                        recipe_description=item.get("recipe_description"),
                    )
                )
    limited = out[: req.num_results or len(out)]
    return SearchResponse(results=limited)
