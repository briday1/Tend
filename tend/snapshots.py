"""Deterministic tether-chat calendar snapshot aggregation (no AI calls)."""
from collections import Counter, defaultdict
from datetime import date, timedelta
from . import store as db

def snapshot(start: str, end: str, category: str = "") -> dict:
    first, last = date.fromisoformat(start), date.fromisoformat(end)
    if last < first or (last-first).days > 365:
        raise ValueError("Date range must be ordered and at most 366 days")
    threads = db.with_categories(db.query("SELECT id,title,category,state,due_at,revisit_at,created_at,archived_at FROM threads WHERE archived_at IS NULL"))
    events = db.with_categories(db.query("SELECT a.thread_id,a.kind,a.body,a.occurred_at,t.title,t.category FROM activity a JOIN threads t ON t.id=a.thread_id WHERE substr(a.occurred_at,1,10)>=? AND substr(a.occurred_at,1,10)<=? ORDER BY a.occurred_at,a.id", (start,end)),"thread_id")
    if category:
        threads = [t for t in threads if category in t["categories"]]
        events = [e for e in events if category in e["categories"]]
    byday = defaultdict(lambda: {"tasks":[], "activity":[]})
    for t in threads:
        due = (t.get("due_at") or "")[:10]
        if start <= due <= end:
            byday[due]["tasks"].append({"id":t["id"],"title":t["title"],"category":t["category"],"categories":t["categories"],"state":t["state"],"date":due,"href":"/board#task/"+t["id"]})
    for e in events:
        day=e["occurred_at"][:10]
        byday[day]["activity"].append({"thread_id":e["thread_id"],"title":e["title"],"category":e["category"],"categories":e["categories"],"kind":e["kind"],"body":e["body"],"occurred_at":e["occurred_at"]})
    days=[]
    cursor=first
    while cursor<=last:
        iso=cursor.isoformat()
        items=byday[iso]
        items["tasks"].sort(key=lambda t:(t["category"].casefold(),t["title"].casefold(),t["id"]))
        days.append({"date":iso,**items})
        cursor+=timedelta(days=1)
    due=[t for d in days for t in d["tasks"]]
    categories=Counter(c for t in due for c in t["categories"])
    kinds=Counter(e["kind"] for e in events)
    return {"start":start,"end":end,"category":category or None,"days":days,
            "insights":{"scheduled_due":len(due),"activity_events":len(events),
                        "active_days":sum(bool(d["activity"]) for d in days),
                        "categories":dict(sorted(categories.items())),
                        "activity_types":dict(sorted(kinds.items()))},
            "notice":"Due dates use current task records, not reconstructed historical states. Activity uses recorded event dates in UTC. No historical state changes are inferred."}
