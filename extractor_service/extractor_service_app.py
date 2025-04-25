import json
import os
from typing import List

import openai
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

load_dotenv(os.path.join(os.path.dirname(__file__), "../.env"))

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


extract_schema = {
    "name": "extract_full_recipe",
    "description": "Parse recipe HTML into structured fields",
    "parameters": {
        "type": "object",
        "properties": {
            "title": {"type": "string"},
            "ingredients": {"type": "array", "items": {"type": "string"}},
            "steps": {"type": "array", "items": {"type": "string"}},
            "tools": {"type": "array", "items": {"type": "string"}},
            "cook_time_mins": {"type": "integer"},
            "source_url": {"type": "string"},
        },
        "required": ["title", "ingredients", "steps", "tools", "source_url"],
    },
}

app = FastAPI(title="Recipe Extractor Service")


@app.post("/extract_recipe", response_model=ExtractResponse)
def extract_recipe(req: ExtractRequest):
    try:
        response = openai.responses.create(
            model="gpt-4o-mini",
            instructions="You are a recipe extraction assistant",
            input=req.html,
            tools=[extract_schema],
            tool_choice="extract_full_recipe",
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"LLM error: {e}")

    choice = (
        response["choices"][0] if isinstance(response, dict) else response.choices[0]
    )
    if isinstance(choice, dict):
        message = choice.get("message", {})
    else:
        message = choice.message

    if isinstance(message, dict):
        arguments_json = message.get("arguments", "{}")
    else:
        arguments_json = message.arguments

    try:
        parsed = json.loads(arguments_json)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Malformed LLM output: {e}")

    return ExtractResponse(
        title=parsed["title"],
        ingredients=parsed["ingredients"],
        steps=parsed["steps"],
        tools=parsed.get("tools", []),
        cook_time_mins=parsed.get("cook_time_mins", 0),
        source_url=parsed["source_url"],
    )
