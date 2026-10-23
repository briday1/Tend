"""MCP stdio interface to the same local SQLite database as the browser app."""
import os
import sys
from mcp.server.fastmcp import FastMCP
from . import store as db
mcp=FastMCP("Tend",host="127.0.0.1",port=int(os.environ.get("TEND_MCP_PORT","8766")))
@mcp.tool()
def get_snapshot(start:str,end:str,category:str="")->dict:
    """Get a read-only calendar for inclusive ISO dates. Each task appears once and carries all categories. A category filter matches any membership; category counts can overlap. Embed the view URL in chat on request; PNG/SVG download URLs need no AI generation."""
    from .snapshots import snapshot
    from urllib.parse import urlencode
    data=snapshot(start,end,category)
    query=urlencode({"start":start,"end":end,**({"category":category} if category else {})})
    data["view_url"]="/snapshots?"+query
    data["downloads"]={format:"/api/snapshot."+format+"?"+query for format in ("png","svg")}
    return data
@mcp.tool()
def task_link(thread_id:str)->dict:
    """Return a clickable local Tend task link, suitable for rich text or fallback navigation."""
    t=db.get(thread_id)
    return {"id":thread_id,"title":t["title"],"href":"/board#task/"+thread_id} if t else {"error":"Thread not found"}
@mcp.tool()
def whats_on_my_mind()->dict:
    """Return open, due, waiting, paused, and settled threads."""
    return db.overview()
@mcp.tool()
def daily_brief()->str:
    """Summarize due, active and waiting items for today."""
    return db.daily_brief()
@mcp.tool()
def due_reminders()->list[dict]:
    """List reminders that are currently due."""
    return db.overview()["due"]
@mcp.tool()
def categories()->list[dict]:
    """Show category groups. A task may belong to several groups; deduplicate by id for overall counts."""
    return db.board()
@mcp.tool()
def find_threads(query:str="")->list[dict]:
    """Search threads and their entries, or list all if no query."""
    return db.list_threads(query)
@mcp.tool()
def explore_thread(thread_id:str)->dict:
    """See full context, chronology, and relationships for a thread."""
    return db.get(thread_id) or {"error":"Thread not found"}
@mcp.tool()
def capture_thought(title:str,summary:str="",categories:list[str]|None=None)->dict:
    """Capture one task, optionally in several categories. Do not create a copy for each category."""
    return db.create(title,summary,categories)
@mcp.tool()
def add_to_thread(thread_id:str,text:str,kind:str="thought")->dict:
    """Add an observation, question, action, decision, or update."""
    return db.add(thread_id,kind,text) or {"error":"Thread not found"}
@mcp.tool()
def revise_thread(thread_id:str,state:str="",summary:str="",revisit_at:str="",due_at:str="")->dict:
    """Update status, summary, or ISO timestamp for next revisit."""
    fields={}
    if state:fields["state"]=state
    if summary:fields["summary"]=summary
    if revisit_at:fields["revisit_at"]=revisit_at
    if due_at:fields["due_at"]=due_at
    return db.update(thread_id,fields) or {"error":"Thread not found"}
@mcp.tool()
def relate_threads(first_id:str,second_id:str)->dict:
    """Connect two related threads."""
    return {"linked":db.link(first_id,second_id)}
@mcp.tool()
def change_category(thread_id:str,category:str)->dict:
    """Replace all memberships with one category. For additional memberships use set_task_categories(mode='add')."""
    return db.update(thread_id,{"category":category}) or {"error":"Thread not found"}
@mcp.tool()
def set_task_categories(thread_id:str,categories:list[str],mode:str="replace")->dict:
    """Set several categories on one task. mode='add' preserves existing categories, 'remove' removes only named memberships, and 'replace' sets the whole list. An empty replacement resets to Unsorted. Returned categories lists every membership."""
    return db.set_categories(thread_id,categories,mode) or {"error":"Thread not found"}
@mcp.tool()
def log_activity(thread_id:str,text:str,kind:str="progress",occurred_at:str="")->dict:
    """Log work or feedback with optional ISO 8601 occurrence timestamp."""
    return db.record_activity(thread_id,text,kind,occurred_at or None) or {"error":"Thread not found"}
@mcp.tool()
def summarize_activity(period:str="week",anchor:str="")->dict:
    """Return structured activity for a week, month, quarter or year."""
    return db.activity_report(period,anchor or None)
@mcp.tool()
def recurring_items()->dict:
    """See all recurring threads and their next occurrences."""
    return {"due":db.recurring_due(),"all":[t for t in db.list_threads() if t.get("recurrence")]}
@mcp.tool()
def set_recurrence(thread_id:str,frequency:str,next_occurrence:str)->dict:
    """Configure a daily, weekly, monthly, quarterly or yearly recurrence."""
    return db.update(thread_id,{"recurrence":frequency,"next_occurrence":next_occurrence}) or {"error":"Thread not found"}
@mcp.tool()
def complete_recurring_occurrence(thread_id:str,description:str="Completed recurring occurrence")->dict:
    """Log completing a cycle and schedule the next recurrence."""
    return db.complete_occurrence(thread_id,description)
@mcp.tool()
def set_task_due_action(thread_id:str,action:str="activity_report",period:str="week",category:str="")->dict:
    """Attach an activity report to a task's reminder (or action='none' to clear)."""
    return db.configure_due_action(thread_id,action,period,category)
@mcp.tool()
def run_task_due_action(thread_id:str,anchor:str="")->dict:
    """Preview a task's linked reporting action, without any AI or modifying its recurrence."""
    return db.report_for_task(thread_id,anchor or None)
@mcp.tool()
def archive_task(thread_id:str)->dict:
    """Archive a task without deleting history."""
    return db.archive_thread(thread_id,True)
@mcp.tool()
def restore_task(thread_id:str)->dict:
    """Restore an archived task."""
    return db.archive_thread(thread_id,False)
@mcp.tool()
def list_archived_tasks(query:str="")->list[dict]:
    """Search archived task records."""
    return db.archived_threads(query)
if __name__=="__main__":
    db.init()
    mcp.run(transport="streamable-http" if "--http" in sys.argv else "stdio")
