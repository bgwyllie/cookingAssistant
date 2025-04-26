from typing import List

import requests
from bs4 import BeautifulSoup
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="HTML Fetcher Service")


class FetchRequest(BaseModel):
    urls: List[str]


class FetchResult(BaseModel):
    url: str
    html: str


class FetchResponse(BaseModel):
    results: List[FetchResult]


@app.post("/fetch_html", response_model=FetchResponse)
def fetch_html(req: FetchRequest):
    results: List[FetchResult] = []
    for url in req.urls:
        try:
            response = requests.get(url, timeout=5)
            response.raise_for_status()
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"Error fetching {url}: {e}")

        soup = BeautifulSoup(response.text, "html.parser")
        for tag in soup(["script", "style"]):
            tag.decompose()

        cleaned_html = str(soup)
        results.append(FetchResult(url=url, html=cleaned_html))

    return FetchResponse(results=results)
