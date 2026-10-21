# Tend

Tend is a local-first home for unfinished thoughts, questions, actions, decisions, and projects. No task hierarchy required.

## Get started

Requires Python 3.11+.

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
uvicorn tend.app:app --host 127.0.0.1 --port 8765
```

Then visit http://127.0.0.1:8765.

SQLite data lives in `~/.tend/tend.sqlite3` unless `TEND_DB` is set. Only run on your local computer; this first prototype has no login/authentication.

## MCP

Run `python -m tend.mcp_server` from your local repository after installing dependencies. Configure an MCP stdio client to execute that command with the repository as its working directory, using the same Python environment as the web app. MCP access allows reading and editing local data, so only use trusted clients.

## Initial features

Capture open loops, record thoughts/actions/questions/decisions/updates, search, set a revisit time, mark something waiting or settled, and browse related threads. MCP tools let an LLM ask what's on your mind and progressively explore or update threads.

AI summaries, semantic search, background nudges, multi-device sync, and hosted access are not yet included. This is a single-user local prototype.
