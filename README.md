# Tend

A local-first personal assistant for unfinished thoughts. Talk naturally: “Remember that I need to look into this,” “What am I tracking?”, “That thing is blocked,” or “I finished it.” Tend keeps its state in SQLite, **not** browser storage.

## Install and start

Python 3.11 or newer.

```bash
git clone https://github.com/briday1/Tend.git
cd Tend
python -m pip install -e .
tend
```

The **single `tend` command** starts the browser web server on http://127.0.0.1:8765 and local MCP streamable-HTTP on http://127.0.0.1:8766/mcp. Press Ctrl+C to stop both. Set `TEND_NO_BROWSER=1` if you don't want your browser to open.

Open **Settings** in the GUI, enter your HTTPS API base URL, model name and your own API key. The model **must support OpenAI-compatible chat-completions tool calling**. The key is stored in `~/.tend/provider.json` (restricted file permissions on platforms that support them). The GUI never receives the stored key; changing or clearing browser data does not remove it. For hosted AI, note that thread context is sent to the configured provider.

## Local storage and MCP

- SQLite: `~/.tend/tend.sqlite3` (override via `TEND_DB`)
- Browser: http://127.0.0.1:8765
- MCP HTTP: http://127.0.0.1:8766/mcp
- MCP stdio alternative: `python -m tend.mcp_server`
- Local backup: **Settings → Download SQLite backup**
- Tests: `python -m pip install -e '.[dev]'` then `pytest`

MCP and the browser use **the same database**. MCP tools can read and update stored information. Both servers listen on loopback only; there is no authentication. Do not expose ports to other machines or untrusted clients. Clients must be trusted, and an accessible MCP port is not a protected security boundary.

## What it does

Conversational capture, question answering from stored threads, completion/waiting status changes, related thoughts, reminders based on explicit revisit dates, searchable history, local SQL storage, BYOK settings, and optional MCP access.

Current limits: reminders are surfaced when browsing (no OS push notifications); natural-language dates depend on the model; no scheduled background agent, automatic backup schedule, multi-device sync, or fully semantic long-term retrieval. The assistant uses a bounded tool-calling loop; providers without tool calling won't support the full experience.
