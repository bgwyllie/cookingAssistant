import os
from typing import List

import openai
from dotenv import load_dotenv
from fastapi import FastAPI
from pydantic import BaseModel

load_dotenv(os.path.join(os.path.dirname(__file__), "../.env"))

openai.api_key = os.environ.get("OPENAI_API_KEY")
if not openai.api_key:
    raise RuntimeError("missing open ai key")


class QueryRequest(BaseModel):
    ingredients: List[str]


class QueryResponse(BaseModel):
    queries: List[str]


app = FastAPI(title="Query Planner Service")


def _unwrap_content(response) -> str:
    choices = (
        response.get("choices", []) if isinstance(response, dict) else response.choices
    )
    if not choices:
        return ""
    first_choice = choices[0]
    message = (
        first_choice.get("message", {})
        if isinstance(first_choice, dict)
        else first_choice.message
    )
    return message.get("content", "") if isinstance(message, dict) else message.content


app = FastAPI(title="Query Planner")


@app.post("/generate_queries", response_model=QueryResponse)
def generate_queries(req: QueryRequest):

    response = openai.responses.create(
        model="gpt-4o-mini",
        instructions="You are a recipe search query generator",
        input=[
            f"I have these ingredients {req.ingredients}. Generate 3-5 concise web search queries that would find recipes matching these constraints. List each query on its own line"
        ],
    )

    text = _unwrap_content(response).strip()
    queries = [line.strip() for line in text.splitlines() if line.strip()]
    return QueryResponse(queries=queries)
