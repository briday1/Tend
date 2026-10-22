import pytest
from fastapi.testclient import TestClient
from tend import store
from tend.app import app

@pytest.fixture
def client(tmp_path,monkeypatch):
    monkeypatch.setenv("TEND_DB",str(tmp_path/"test.sqlite3"))
    store.init()
    return TestClient(app)

def test_capture_search_revisit_and_delete(client):
    t=client.post("/api/threads",json={"title":"Think about this"}).json()
    id=t["id"]
    assert client.get("/api/threads?q=Think").json()[0]["id"]==id
    note=client.post(f"/api/threads/{id}/entries",json={"kind":"action","body":"Try something"}).json()
    assert client.patch("/api/entries/"+note["id"],json={"done":True}).json()["done"]==1
    assert len(client.get("/api/threads?q=Try").json())==1
    assert client.patch("/api/threads/"+id,json={"revisit_at":"2020-01-01T00:00:00Z","state":"waiting"}).status_code==200
    assert client.get("/api/overview").json()["due"][0]["id"]==id
    assert client.delete("/api/threads/"+id).json()["deleted"] is True

def test_related_and_home(client):
    a=client.post("/api/threads",json={"title":"A"}).json()["id"]
    b=client.post("/api/threads",json={"title":"B"}).json()["id"]
    assert client.post("/api/threads/"+a+"/links",json={"other_id":b}).status_code==200
    assert client.get("/api/threads/"+b).json()["related"][0]["id"]==a
    assert client.get("/").status_code==200

def test_board_category_and_manual_edit(client):
    thought=client.post("/api/threads",json={"title":"Experiment with a new interface"}).json()
    id=thought["id"]
    response=client.patch(f"/api/threads/{id}",json={"category":"Product ideas","summary":"Try different views","state":"waiting"})
    assert response.status_code==200
    assert response.json()["category"]=="Product ideas"
    board=client.get("/api/board")
    assert board.status_code==200
    assert any(x["name"]=="Product ideas" and x["threads"][0]["id"]==id for x in board.json())
    assert client.get("/board").status_code==200

def test_markdown_is_sanitized_and_formatted():
    from tend.rendering import render
    html = render("**Bold** and *italic*\n\n- one\n- two\n\n<script>alert(1)</script>")
    assert "<strong>Bold</strong>" in html
    assert "<em>italic</em>" in html
    assert "<li>" in html
    assert "<script>" not in html
    assert "alert(1)" in html

def test_rendered_history(client):
    from tend import store
    store.remember("assistant","A **formatted** response")
    result = client.get("/api/conversation/rendered")
    assert result.status_code == 200
    assert "<strong>formatted</strong>" in result.json()[-1]["html"]

def test_theme_assets(client):
    css=client.get("/theme.css")
    js=client.get("/theme.js")
    assert css.status_code==200 and "--accent" in css.text
    assert js.status_code==200 and "data-theme-picker" in js.text
    assert 'href="/theme.css"' in client.get("/").text
    assert 'href="/theme.css"' in client.get("/board").text
