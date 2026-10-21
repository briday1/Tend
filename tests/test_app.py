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
