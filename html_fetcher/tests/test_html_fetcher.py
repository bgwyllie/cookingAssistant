import os

import pytest
from fastapi.testclient import TestClient
from html_fetcher_app import app

mock_HTML = """
<html>
<head><title>Test</title><style>body{}</style></head>
<body>
<h1>Header</h1>
<script>alert("x")</script>
<p>Content</p>
</body>
</html>
"""


class MockResponse:
    def __init__(self, text):
        self.text = text
        self.status_code = 200

    def raise_for_status(self):
        pass


@pytest.fixture(autouse=True)
def patch_requests(monkeypatch):
    import requests

    monkeypatch.setattr(requests, "get", lambda url, timeout: MockResponse(mock_HTML))


client = TestClient(app)


def test_fetch_html_strips_scripts_and_styles():
    payload = {"urls": ["http://example.com"]}
    res = client.post("/fetch_html", json=payload)
    assert res.status_code == 200, res.text

    data = res.json()
    assert "results" in data
    assert len(data["results"]) == 1

    result = data["results"][0]
    assert result["url"] == "http://example.com"
    html = result["html"].lower()

    assert "<h1>header</h1>" in html
    assert "<p>content</p>" in html

    assert "<script" not in html
    assert "<style" not in html
