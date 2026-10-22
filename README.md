# Tend

Tend is a local-first place to capture what's on your mind and return to it naturally. Its browser interface uses chat for capture and exploration, with reminders and threads alongside. No up-front classification is needed.

## Run locally

Requires Python 3.11+.

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
python -m pip install -e .
uvicorn tend.app:app --host 127.0.0.1 --port 8765
```

Open http://127.0.0.1:8765.

Local data is stored in `~/.tend/tend.sqlite3`, or at `TEND_DB` if set. The web server binds to loopback only when started with the command above. There is no authentication, so do not expose it on a network.

## Optional AI conversation

Tend still captures and browses thoughts without an AI key. To enable conversational exploration, set `TEND_AI_API_KEY` **on the local server** before starting Tend. Optionally set `TEND_AI_MODEL` (default `gpt-4.1-mini`) and `TEND_AI_BASE_URL` (default `https://api.openai.com/v1`) for a compatible chat completions endpoint. The browser does not store the key.

When you ask a question, relevant saved thoughts may be sent to your configured AI provider for reflection. Do not use an untrusted provider with private notes.

## MCP

Start with `python -m tend.mcp_server` and point your MCP stdio client to this command in Tend's Python environment. MCP clients can access and modify your local threads; use only trusted clients.

## Scope

Single-user local prototype: capture, search, linked threads, notes, optional AI reflection, chat and a reminders view. No background notifications, automatic semantic grouping, remote synchronization, or hosted account yet. Reminders surface within the browser when it is open.
