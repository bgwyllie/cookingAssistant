import json
import os
from typing import List

import openai
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

openai.api_key = os.getenv("OPENAI_API_KEY")
if not openai.api_key:
    raise RuntimeError("missing open ai key")


class ExtractRequest(BaseModel):
    url: str
    html: str


class ExtractResponse(BaseModel):
    title: str
    ingredients: List[str]
    steps: List[str]
    tools: List[str]
    cook_time_mins: int
    source_url: str


recipe_schema = {
    "type": "object",
    "properties": {
        "title": {"type": "string"},
        "ingredients": {"type": "array", "items": {"type": "string"}},
        "steps": {"type": "array", "items": {"type": "string"}},
        "tools": {"type": "array", "items": {"type": "string"}},
        "cook_time_mins": {"type": "integer"},
        "source_url": {"type": "string"},
    },
    "required": [
        "title",
        "ingredients",
        "steps",
        "tools",
        "cook_time_mins",
        "source_url",
    ],
    "additionalProperties": False,
}

app = FastAPI(title="Recipe Extractor Service")


@app.post("/extract_recipe", response_model=ExtractResponse)
def extract_recipe(req: ExtractRequest):
    try:
        response = openai.responses.create(
            model="gpt-4o-mini",
            instructions=(
                "You are a recipe extraction assistant"
                "Parse the provided HTML and return only a JSON object that matches exactly the schema"
            ),
            input=req.html,
            text={
                "format": {
                    "type": "json_schema",
                    "name": "extract_full_recipe",
                    "schema": recipe_schema,
                    "strict": True,
                }
            },
            stream=False,
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"LLM error: {e}")

    json_string = getattr(response, "output_text", None)
    if not json_string:
        raise HTTPException(status_code=500, detail="Model returned no JSON")

    try:
        parsed = json.loads(json_string)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Malformed JSON from model {e}")
    return ExtractResponse(**parsed)
