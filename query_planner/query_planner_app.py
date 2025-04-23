import os
from typing import List, Optional

import openai
from dotenv import load_dotenv
from fastapi import FastAPI
from pydantic import BaseModel

load_dotenv("../../.env")

openai.api_key = os.getenv("OPENAI_API_KEY")


class QueryRequest(BaseModel):
    ingredients: List[str]
    # cuisine: Optional[str] = None
    # max_cook_time_mins: Optional[int] = None
    # dietary_restrictions: Optional[str] = None


class QueryResponse(BaseModel):
    queries: List[str]


app = FastAPI(title="Query Planner Service")


@app.post("/generate_queries", response_model=QueryResponse)
def generate_queries(req: QueryRequest):
    system = {"role": "system", "content": "You are a recipe search query generator"}
    user_prompt = f"""
    I have these ingredients {req.ingredients}
    Generate 3-5 concise web search queries that would find recipes matching these constraints.
    List each query on its own line
    """

    user = {"role": "user", "content": user_prompt}

    response = openai.ChatCompletion.create(
        model="gpt-4o-mini", messages=[system, user], temperature=0.7, max_tokens=100
    )

    text = response.choices[0].message.content.strip()
    queries = [q.strip() for q in text.split("\n") if q.strip()]
    return QueryResponse(queries=queries)
