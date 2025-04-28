import json
import os
from typing import List

import openai
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

openai.api_key = os.getenv("OPENAI_API_KEY")
if not openai.api_key:
    raise RuntimeError("missing open ai key")


class QueryRequest(BaseModel):
    ingredients: str


class QueryResponse(BaseModel):
    queries: List[str]


app = FastAPI(title="Query Planner Service")


@app.post("/generate_queries", response_model=QueryResponse)
def generate_queries(req: QueryRequest):
    prompt = (
        f"I have the following ingredients and/or recipe requirements for my meal: {req.ingredients}."
        "Generate 3 concise web search queries that would find recipes matching these constraints, each on its own line"
    )

    try:
        response = openai.responses.create(
            model="gpt-4.1-mini",
            instructions="You are a recipe search query generator",
            input=prompt,
        )
    except openai.OpenAIError as e:
        raise HTTPException(status_code=502, detail=f"OpenAI error: {e}")

    if isinstance(response, dict):
        data = response
    elif hasattr(response, "to_dict"):
        data = response.to_dict()
    else:
        try:
            data = dict(response)
        except Exception:
            raise HTTPException(
                status_code=500, detail=f"cannot convert response to dict {response}"
            )

    messages = data.get("output", [])
    if not messages:
        raise HTTPException(
            status_code=500, detail=f"no output message {json.dumps(data)}"
        )

    first_message = messages[0]
    content = first_message.get("content")
    if not content:
        raise HTTPException(
            status_code=500,
            detail=f"no content in first output message: {json.dumps(first_message)}",
        )
    text = "".join(chunk.get("text", "") for chunk in content).strip()
    queries = [line.strip() for line in text.splitlines() if line.strip()]

    return QueryResponse(queries=queries)
