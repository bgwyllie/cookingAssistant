import json
import os
from typing import Dict, List

import openai
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

load_dotenv(os.path.join(os.path.dirname(__file__), "../.env"))

openai.api_key = os.getenv("OPENAI_API_KEY")
if not openai.api_key:
    raise RuntimeError("missing open ai key")


class Recipe(BaseModel):
    id: str
    title: str
    ingredients: List[str]
    steps: List[str]
    tools: List[str]
    cook_time_mins: int
    source_url: str


class RankRequest(BaseModel):
    requirements: Dict[str, List[str]]
    recipes: List[Recipe]
    top_k: int = 5


class RankResponse(BaseModel):
    recipes: List[Recipe]


rank_schema = {
    "name": "rank_recipes",
    "description": "given user requirements and found recipes, return the recipe urls ranked best to worst",
    "parameters": {
        "type": "object",
        "properties": {"ranked_ids": {"type": "array", "items": {"type": "string"}}},
        "required": ["ranked_ids"],
    },
}

app = FastAPI(title="Recipe Ranker Service")


@app.post("/rank_recipes", response_model=RankResponse)
def rank_recipes(req: RankRequest):
    try:
        resp = openai.responses.create(
            model="gpt-4o-mini",
            instructions="You are a recipe ranking assistant",
            input=json.dumps([r.model_dump() for r in req.recipes]),
            tools=[rank_schema],
            tool_choice="rank_recipes",
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"LLM error: {e}")

    choice = resp["choices"][0] if isinstance(resp, dict) else resp.choices[0]
    message = choice.get("message", {}) if isinstance(choice, dict) else choice.message
    arguments = (
        message.get("arguments", "{}")
        if isinstance(message, dict)
        else message.arguments
    )

    try:
        out = json.loads(arguments)
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=500, detail=f"Malformed LLM output: {e}")

    ranked_ids = out.get("ranked_ids", [])
    top_ids = ranked_ids[: req.top_k]

    reorder_by_id = {r.id: r for r in req.recipes}
    top_recipes = [reorder_by_id[i] for i in top_ids if i in reorder_by_id]

    return RankResponse(recipes=top_recipes)
