from pathlib import Path
from datetime import datetime
from fastapi import FastAPI,HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel,Field
from typing import Literal
from . import store as db

app=FastAPI(title="Tend")
db.init()
class Thread(BaseModel):
    title:str=Field(min_length=1,max_length=300)
    summary:str=""
class Change(BaseModel):
    title:str|None=None
    summary:str|None=None
    state:Literal["open","waiting","paused","settled"]|None=None
    revisit_at:datetime|None=None
class Entry(BaseModel):
    kind:Literal["thought","question","action","decision","update"]="thought"
    body:str=Field(min_length=1)
class Done(BaseModel):
    done:bool
class Relation(BaseModel):
    other_id:str
def found(x):
    if x is None:raise HTTPException(404,"Not found")
    return x
@app.get("/")
def home():return FileResponse(Path(__file__).with_name("index.html"))
@app.get("/api/threads")
def threads(q:str=""):return db.list_threads(q)
@app.get("/api/overview")
def overview():return db.overview()
@app.post("/api/threads",status_code=201)
def create(data:Thread):return db.create(data.title,data.summary)
@app.get("/api/threads/{id}")
def get(id:str):return found(db.get(id))
@app.patch("/api/threads/{id}")
def change(id:str,data:Change):
    fields=data.model_dump(exclude_unset=True)
    if fields.get("revisit_at"):fields["revisit_at"]=fields["revisit_at"].isoformat()
    return found(db.update(id,fields))
@app.delete("/api/threads/{id}")
def delete(id:str):return {"deleted":db.delete(id)}
@app.post("/api/threads/{id}/entries",status_code=201)
def add(id:str,data:Entry):return found(db.add(id,data.kind,data.body))
@app.patch("/api/entries/{id}")
def done(id:str,data:Done):return found(db.toggle(id,data.done))
@app.post("/api/threads/{id}/links")
def link(id:str,data:Relation):
    if not db.link(id,data.other_id):raise HTTPException(404,"Thread not found")
    return db.get(id)
