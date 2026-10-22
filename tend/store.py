import os, sqlite3
from pathlib import Path
from uuid import uuid4
from datetime import datetime, timezone
from contextlib import contextmanager

def now(): return datetime.now(timezone.utc).isoformat()
def path(): return Path(os.environ.get("TEND_DB", Path.home()/".tend"/"tend.sqlite3")).expanduser()
@contextmanager
def conn():
    p=path();p.parent.mkdir(parents=True,exist_ok=True)
    c=sqlite3.connect(p);c.row_factory=sqlite3.Row;c.execute("PRAGMA foreign_keys=ON")
    try: yield c;c.commit()
    finally: c.close()
def init():
    with conn() as c:
        c.executescript("""
CREATE TABLE IF NOT EXISTS threads(id TEXT PRIMARY KEY,title TEXT NOT NULL,summary TEXT NOT NULL DEFAULT '',state TEXT NOT NULL DEFAULT 'open',revisit_at TEXT,created_at TEXT NOT NULL,updated_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS entries(id TEXT PRIMARY KEY,thread_id TEXT NOT NULL REFERENCES threads(id) ON DELETE CASCADE,kind TEXT NOT NULL,body TEXT NOT NULL,done INTEGER NOT NULL DEFAULT 0,created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS relations(a TEXT NOT NULL REFERENCES threads(id) ON DELETE CASCADE,b TEXT NOT NULL REFERENCES threads(id) ON DELETE CASCADE,PRIMARY KEY(a,b));
CREATE TABLE IF NOT EXISTS conversation(id TEXT PRIMARY KEY,role TEXT NOT NULL,body TEXT NOT NULL,created_at TEXT NOT NULL);
""")
        columns={row[1] for row in c.execute("PRAGMA table_info(threads)")}
        if "category" not in columns:c.execute("ALTER TABLE threads ADD COLUMN category TEXT NOT NULL DEFAULT 'Unsorted'")
        if "notified_for" not in columns:c.execute("ALTER TABLE threads ADD COLUMN notified_for TEXT")
def query(sql,args=()):
    with conn() as c: return [dict(r) for r in c.execute(sql,args)]
def get(id):
    rows=query("SELECT * FROM threads WHERE id=?",(id,))
    if not rows:return None
    t=rows[0];t["entries"]=query("SELECT * FROM entries WHERE thread_id=? ORDER BY created_at,id",(id,))
    t["related"]=query("SELECT t.id,t.title FROM relations r JOIN threads t ON t.id=CASE WHEN r.a=? THEN r.b ELSE r.a END WHERE r.a=? OR r.b=?",(id,id,id))
    return t
def list_threads(q=""):
    rows=query("SELECT t.*,(SELECT COUNT(*) FROM entries e WHERE e.thread_id=t.id) entry_count FROM threads t WHERE title LIKE ? OR summary LIKE ? OR EXISTS(SELECT 1 FROM entries e WHERE e.thread_id=t.id AND e.body LIKE ?) ORDER BY updated_at DESC",("%"+q+"%",)*3)
    for t in rows:t["due"]=bool(t["revisit_at"] and t["revisit_at"]<=now() and t["state"]!="settled")
    return sorted(rows,key=lambda t:not t["due"])
def create(title,summary=""):
    if not title.strip():raise ValueError("Title required")
    id=uuid4().hex;t=now()
    with conn() as c:c.execute("INSERT INTO threads(id,title,summary,created_at,updated_at) VALUES(?,?,?,?,?)",(id,title.strip(),summary,t,t))
    return get(id)
def update(id,fields):
    allowed={"title","summary","state","revisit_at","category"}
    fields={k:v for k,v in fields.items() if k in allowed}
    if "category" in fields and (not isinstance(fields["category"],str) or not fields["category"].strip() or len(fields["category"])>80):raise ValueError("Invalid category")
    if "state" in fields and fields["state"] not in {"open","waiting","paused","settled"}:raise ValueError("Invalid state")
    if "title" in fields and not fields["title"].strip():raise ValueError("Title required")
    if fields:
        if "revisit_at" in fields:fields["notified_for"]=None
        fields["updated_at"]=now()
        with conn() as c:c.execute("UPDATE threads SET "+",".join(k+"=?" for k in fields)+" WHERE id=?",(*fields.values(),id))
    return get(id)
def add(id,kind,body):
    if kind not in {"thought","question","action","decision","update"}:raise ValueError("Invalid kind")
    if not body.strip():raise ValueError("Entry required")
    if not get(id):return None
    eid=uuid4().hex;t=now()
    with conn() as c:
        c.execute("INSERT INTO entries(id,thread_id,kind,body,created_at) VALUES(?,?,?,?,?)",(eid,id,kind,body.strip(),t))
        c.execute("UPDATE threads SET updated_at=? WHERE id=?",(t,id))
    return query("SELECT * FROM entries WHERE id=?",(eid,))[0]
def toggle(id,done):
    with conn() as c:c.execute("UPDATE entries SET done=? WHERE id=? AND kind='action'",(int(done),id))
    rows=query("SELECT * FROM entries WHERE id=?",(id,))
    return rows[0] if rows else None
def link(a,b):
    if a==b:raise ValueError("Self-link")
    if not get(a) or not get(b):return False
    with conn() as c:c.execute("INSERT OR IGNORE INTO relations(a,b) VALUES(?,?)",tuple(sorted([a,b])))
    return True
def delete(id):
    with conn() as c:return bool(c.execute("DELETE FROM threads WHERE id=?",(id,)).rowcount)
def overview():
    rows=list_threads()
    return {"due":[t for t in rows if t["due"]],"active":[t for t in rows if t["state"]=="open" and not t["due"]],"waiting":[t for t in rows if t["state"]=="waiting"],"paused":[t for t in rows if t["state"]=="paused"],"settled":[t for t in rows if t["state"]=="settled"]}

def conversation(limit=100):
    return list(reversed(query("SELECT * FROM conversation ORDER BY created_at DESC,id DESC LIMIT ?",(limit,))))
def remember(role,body):
    id=uuid4().hex
    with conn() as c:c.execute("INSERT INTO conversation(id,role,body,created_at) VALUES(?,?,?,?)",(id,role,body,now()))
    return id

def board():
    groups={}
    for t in list_threads():
        category=t.get("category") or "Unsorted"
        groups.setdefault(category,[]).append(t)
    return [{"name":name,"threads":items} for name,items in sorted(groups.items(),key=lambda x:(x[0]=="Unsorted",x[0].casefold()))]

def claim_notifications():
    """Claim due reminders once per scheduled time."""
    from datetime import datetime,timezone,timedelta
    current=datetime.now(timezone.utc)
    claimed=[]
    with conn() as c:
        rows=c.execute("SELECT id,title,revisit_at FROM threads WHERE revisit_at IS NOT NULL AND state!='settled' AND (notified_for IS NULL OR notified_for!=revisit_at)").fetchall()
        for row in rows:
            try:due=datetime.fromisoformat(row["revisit_at"].replace("Z","+00:00"))
            except ValueError:continue
            if due.tzinfo is None:continue
            if current-timedelta(hours=24)<=due<=current and len(claimed)<3:
                c.execute("UPDATE threads SET notified_for=? WHERE id=?",(row["revisit_at"],row["id"]))
                claimed.append(dict(row))
    return claimed

def daily_brief():
    data=overview()
    lines=["# Daily brief","","## Ready to revisit"]
    lines.extend("- **"+t["title"]+"**" for t in data["due"][:15])
    if not data["due"]:lines.append("Nothing due right now.")
    lines+=["","## In progress"]
    lines.extend("- "+t["title"] for t in data["active"][:10])
    if not data["active"]:lines.append("Nothing active.")
    lines+=["","## Waiting on"]
    lines.extend("- "+t["title"] for t in data["waiting"][:10])
    if not data["waiting"]:lines.append("Nothing waiting.")
    lines+=["",f"Tracking {len(list_threads())} things in total."]
    return "\n".join(lines)
