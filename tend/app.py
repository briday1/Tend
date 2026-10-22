from pathlib import Path
import re
from datetime import datetime
from fastapi import FastAPI,HTTPException
from fastapi.responses import FileResponse
from starlette.middleware.trustedhost import TrustedHostMiddleware
from pydantic import BaseModel,Field
from typing import Literal
from . import store as db
from . import ai
from .ai import reflect

app=FastAPI(title="Tend")
app.add_middleware(TrustedHostMiddleware,allowed_hosts=["127.0.0.1","localhost","[::1]"])
db.init()
class Ask(BaseModel):
    question:str=Field(min_length=1,max_length=1000)
class Thread(BaseModel):
    title:str=Field(min_length=1,max_length=300)
    summary:str=""
class Change(BaseModel):
    title:str|None=None
    summary:str|None=None
    category:str|None=None
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
@app.get("/board")
def board_page():return FileResponse(Path(__file__).with_name("board.html"))
@app.get("/api/board")
def board():return db.board()
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

@app.post("/api/reflect")
def reflection(data:Ask):
    try:return reflect(data.question)
    except ValueError as exc:raise HTTPException(502,str(exc)) from exc

class Message(BaseModel):
    text:str=Field(min_length=1,max_length=6000)
class Provider(BaseModel):
    base_url:str
    model:str
    api_key:str|None=None
    clear_key:bool=False

@app.get("/api/settings")
def settings():return ai.public_config()

@app.post("/api/settings")
def settings_save(data:Provider):
    try:return ai.save(data.base_url,data.model,data.api_key,data.clear_key)
    except ValueError as exc:raise HTTPException(422,str(exc)) from None

@app.get("/api/conversation")
def history():return db.conversation()

@app.post("/api/chat")
def chat(data:Message):
    message=data.text.strip()
    if not message:raise HTTPException(422,"Message required")
    try:result=ai.chat(message)
    except ValueError as exc:raise HTTPException(502,str(exc)) from exc
    db.remember("user",message)
    db.remember("assistant",result["answer"])
    return {"answer":result["answer"],"actions":result["actions"],"history":db.conversation()}

@app.get("/api/backup")
def backup():
    from fastapi.responses import FileResponse
    from starlette.background import BackgroundTask
    from tempfile import NamedTemporaryFile
    import sqlite3
    import os
    file=NamedTemporaryFile(prefix="tend-backup-",suffix=".sqlite3",delete=False)
    file.close()
    try:
        with sqlite3.connect(db.path()) as src, sqlite3.connect(file.name) as dest:src.backup(dest)
    except Exception:
        os.unlink(file.name)
        raise
    return FileResponse(file.name,filename="tend-backup.sqlite3",media_type="application/octet-stream",
                        background=BackgroundTask(os.unlink,file.name))
