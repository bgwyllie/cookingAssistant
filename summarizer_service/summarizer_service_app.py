import os
from typing import List

import openai
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

openai.api_key = os.getenv("OPENAI_API_KEY")
if not openai.api_key:
    raise RuntimeError("missing open ai key")


class SummarizeRequest(BaseModel):
    title: str
    ingredients: List[str]
    steps: List[str]
    tools: List[str]
    cook_time_mins: int
    source_url: str


class SummarizeResponse(BaseModel):
    summary: str


app = FastAPI(title="Summary Generator Service")


@app.post("/summarize_recipe", response_model=SummarizeResponse)
def summarize_recipe(req: SummarizeRequest):
    try:
        resp = openai.responses.create(
            model="gpt-4o-mini",
            instructions="You are a recipe summarizer",
            input=(
                f"Write a 2–3 sentence summary of this recipe.\n"
                f"Title: {req.title}\n"
                f"Ingredients: {', '.join(req.ingredients)}\n"
                f"Steps: {len(req.steps)} steps\n"
                f"Tools: {', '.join(req.tools)}\n"
                f"Cook time: {req.cook_time_mins} minutes\n"
                f"Source: {req.source_url}\n\n"
                "Summary:"
            ),
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"LLM error: {e}")

    # content = ""
    if isinstance(resp, dict):
        choices = resp.get("choices", [])
        # text = choices[0]["message"]["content"]
        # first = choices[0] if choices else {}
        # msg = first.get("message", {}) if isinstance(first, dict) else {}
        # content = msg.get("content", "")
    else:
        choices = getattr(resp, "choices", [])
        # text = choices[0].message.content
    if not choices:
        text = ""
        # choice = resp.get("choices", [{}])[0]
        # first = choices[0] if choices else {}
        # message = first.get("message", {})
        # text = message.get("content", "")
    else:
        first = choices[0]

        if isinstance(first, dict):
            message = first.get("message", {}) or first
        else:
            message = getattr(first, "message", {}) or first

        if isinstance(message, dict):
            text = message.get("content", "")
        else:
            text = getattr(message, "content", "")
        # choice = resp.choices[0] if resp.choices else None
        # first = choices[0] if choices else None
        # message = getattr(first, "message", {}) if first else {}
        # if isinstance(message, dict):
        #     text = message.get("content", "")
        # else:
        #     text = getattr(message, "content", "")
    # message = choice.get("message", {}) if isinstance(choice, dict) else getattr(choice, "message", {})

    # if isinstance(message, dict):
    #     text = message.get("content", "")
    # else:
    # text = getattr(message, "content", "")

    return SummarizeResponse(summary=text.strip())
