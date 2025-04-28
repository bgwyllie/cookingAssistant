import json
import os
from typing import Dict, List

import openai
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

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
    requirements: Dict[str, str]
    recipes: List[Recipe]
    top_k: int = 3


class RankResponse(BaseModel):
    recipes: List[Recipe]


rank_schema = {
    "type": "object",
    "description": "given user requirements and found recipes, return the recipe urls ranked best to worst",
    "properties": {"ranked_ids": {"type": "array", "items": {"type": "string"}}},
    "required": ["ranked_ids"],
    "additionalProperties": False,
}

app = FastAPI(title="Recipe Ranker Service")


@app.post("/rank_recipes", response_model=RankResponse)
def rank_recipes(req: RankRequest):
    prompt_lines = [
        "You are a recipe ranking assistant.",
        f"Requirements: {json.dumps(req.requirements)}",
        "Recipes:",
    ]

    for recipe in req.recipes:
        prompt_lines.append(
            f"- ID: {recipe.id}, Title: {recipe.title}, Ingredients: {json.dumps(recipe.ingredients)}"
        )
    prompt_lines.append(
        'Return a JSON object with a single key "ranked_ids"\ containing the recipe IDs from best to worst'
    )
    prompt = "\n".join(prompt_lines)
    try:
        response = openai.responses.create(
            model="gpt-4.1-mini",
            input=prompt,
            text={
                "format": {
                    "type": "json_schema",
                    "name": "ranking",
                    "schema": rank_schema,
                    "strict": True,
                }
            },
            stream=False,
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"LLM error: {e}")

    json_text = getattr(response, "output_text", None)
    if not json_text:
        raise HTTPException(status_code=502, detail="Model did not return output_text")

    try:
        parsed = json.loads(json_text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Malformed JSON output: {e}")

    ranked_ids = parsed.get("ranked_ids", [])
    if not isinstance(ranked_ids, list):
        raise HTTPException(status_code=500, detail="`ranked_ids` is not an array")

    top_ids = ranked_ids[: req.top_k]
    id_map = {r.id: r for r in req.recipes}
    top_recipes = [id_map[i] for i in top_ids if i in id_map]

    return RankResponse(recipes=top_recipes)
