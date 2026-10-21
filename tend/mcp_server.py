"""MCP stdio interface to the same local SQLite database as the browser app."""
from mcp.server.fastmcp import FastMCP
from . import store as db
mcp=FastMCP("Tend")
@mcp.tool()
def whats_on_my_mind()->dict:
    """Return open, due, waiting, paused, and settled threads."""
    return db.overview()
@mcp.tool()
def find_threads(query:str="")->list[dict]:
    """Search threads and their entries, or list all if no query."""
    return db.list_threads(query)
@mcp.tool()
def explore_thread(thread_id:str)->dict:
    """See full context, chronology, and relationships for a thread."""
    return db.get(thread_id) or {"error":"Thread not found"}
@mcp.tool()
def capture_thought(title:str,summary:str="")->dict:
    """Capture an idea, concern, intention, or other open loop."""
    return db.create(title,summary)
@mcp.tool()
def add_to_thread(thread_id:str,text:str,kind:str="thought")->dict:
    """Add an observation, question, action, decision, or update."""
    return db.add(thread_id,kind,text) or {"error":"Thread not found"}
@mcp.tool()
def revise_thread(thread_id:str,state:str="",summary:str="",revisit_at:str="")->dict:
    """Update status, summary, or ISO timestamp for next revisit."""
    fields={}
    if state:fields["state"]=state
    if summary:fields["summary"]=summary
    if revisit_at:fields["revisit_at"]=revisit_at
    return db.update(thread_id,fields) or {"error":"Thread not found"}
@mcp.tool()
def relate_threads(first_id:str,second_id:str)->dict:
    """Connect two related threads."""
    return {"linked":db.link(first_id,second_id)}
if __name__=="__main__":
    db.init()
    mcp.run(transport="stdio")
