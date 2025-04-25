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
    prompt = (
        f"Write a 2–3 sentence summary of this recipe.\n"
        f"Title: {req.title}\n"
        f"Ingredients: {', '.join(req.ingredients)}\n"
        f"Steps: {len(req.steps)} steps\n"
        f"Tools: {', '.join(req.tools)}\n"
        f"Cook time: {req.cook_time_mins} minutes\n"
        f"Source: {req.source_url}\n\nSummary"
    )

    try:
        resp = openai.responses.create(
            model="gpt-4o-mini",
            instructions="You are a recipe summarizer",
            input=prompt,
            max_output_tokens=150,
        )
    except openai.OpenAIError as e:
        raise HTTPException(status_code=502, detail=f"LLM error: {e}")

    text = getattr(resp, "output_text", None)
    if text:
        return SummarizeResponse(summary=text.strip())
    print("text", text)
    data = resp.to_dict() if hasattr(resp, "to_dict") else dict(resp)
    print("data", data)
    output = data.get("output", [])
    if not output:
        raise HTTPException(status_code=500, detail="No output from model")
    print("output", output)
    first = output[0]
    print("first", first)
    content_chunks = first.get("content", [])
    if not content_chunks:
        raise HTTPException(status_code=500, detail="No content from model output")
    print("content", content_chunks)
    summary = "".join(chunk.get("text", "") for chunk in content_chunks).strip()
    if not summary:
        raise HTTPException(status_code=500, detail="Empty summary text")
    print("summart", summary)
    return SummarizeResponse(summary=summary)
