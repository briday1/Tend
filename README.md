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

The **single `tend` command** waits for the web server to respond successfully before opening a browser tab, and starts the browser web server on http://127.0.0.1:8765 and local MCP streamable-HTTP on http://127.0.0.1:8766/mcp. Press Ctrl+C to stop both. Set `TEND_NO_BROWSER=1` if you don't want your browser to open.

Open **Settings** in the GUI, enter your HTTPS API base URL, model name and your own API key. The model **must support OpenAI-compatible chat-completions tool calling**. The key is stored in the operating system credential vault (Windows Credential Manager, macOS Keychain, or a supported Linux Secret Service/KWallet backend), NOT in `provider.json`. Only the nonsecret provider URL and model are saved in `~/.tend/provider.json`. The GUI never receives a stored key or exposes a show-key control; changing or clearing browser data does not remove it. If no secure vault is available, key saving fails closed; you can alternatively supply `TEND_AI_API_KEY` as a process environment variable. Existing plaintext keys from early Tend builds are migrated on next settings load when a secure vault is available. Because older versions previously wrote the key unencrypted, consider rotating that key. For hosted AI, note that thread context is sent to the configured provider.

## Local storage and MCP

- SQLite: `~/.tend/tend.sqlite3` (override via `TEND_DB`)
- Browser: http://127.0.0.1:8765
- MCP HTTP: http://127.0.0.1:8766/mcp
- MCP stdio alternative: `python -m tend.mcp_server`
- Local backup: **Settings → Download SQLite backup**
- Tests: `python -m pip install -e '.[dev]'` then `pytest`

MCP and the browser use **the same database**. MCP tools can read and update stored information. Both servers listen on loopback only; there is no authentication. Do not expose ports to other machines or untrusted clients. Clients must be trusted, and an accessible MCP port is not a protected security boundary.

## What it does

Conversation and a separate categorized Board with shared top navigation, five local color themes (Sage, Ocean, Clay, Violet, Graphite), searchable category columns, AI-assisted automatic grouping, manual card editing (title, category, details, status and revisit date), accumulated notes, completion/waiting status changes, searchable history, local SQL storage, BYOK settings, and optional MCP access. On the Board, choose **Ask AI to organize** to draft an instruction in Conversation, review it, and send it. The AI can also choose categories while capturing new thoughts. Both views operate on the same underlying SQLite records.

Current limits: reminders are surfaced when browsing (no OS push notifications); natural-language dates depend on the model; no scheduled background agent, automatic backup schedule, multi-device sync, or fully semantic long-term retrieval. The assistant uses a bounded tool-calling loop; providers without tool calling won't support the full experience.

## Key security

The API key input uses a password field, autocomplete disabled, and is cleared after saving. The GET settings endpoint returns only `has_key`, model, and URL. Saved credentials stay in the operating system vault. No credential ever belongs in the SQLite database, a browser cache, or the Git repository. Avoid running Tend behind a public reverse proxy, or using an untrusted model provider. A previously saved key from versions before the vault migration may exist in filesystem backups, disk history, or snapshots; rotate it if exposure is a concern.

The selected color theme is a display preference kept in browser local storage, separate from SQLite content; clearing browser data resets only the theme, not thoughts or conversations.

## Daily brief and commands

The Conversation view includes a **/ Commands** reference button (or type `/` in an empty message). Commands work locally without an AI request:

- `/brief` — due, active and waiting overview
- `/due` — reminders ready to revisit
- `/waiting` — blocked or waiting items
- `/recent` — recently changed topics
- `/board` — board navigation hint
- `/help` — command reference

Ask the assistant for a daily brief conversationally to get an AI-interpreted answer from the same stored information.

## Desktop notifications and Attention

Running `tend` now starts three local components: the browser web server, MCP HTTP server, and desktop notification worker. The worker polls for due reminders every 20 seconds and attempts OS desktop notifications. Notifications require an active desktop session and OS notification support; they do not run while Tend is stopped or the computer is off. To avoid storms of stale popups, the worker only notifies reminders due within the previous 24 hours, at most three per polling cycle; older items remain visible in Tend. Due reminders are marked as attempted at most once per schedule, including across restarts. Operating-system permissions and platform support may affect whether a popup is actually shown.

The right-side **Attention** panel is selected by the configured AI model rather than displaying every open thread. It shows at most five items, can show none, and caches choices for ten minutes or until recorded threads change. The refresh control asks the AI to reconsider. With no AI connection or a failed AI response, the panel falls back to explicit due reminders only.

Conversation and Board share the same top navigation geometry.

## Appearance

Tend uses the same named theme color definitions as WriteShape: Light, Dark, Solarized Light, Solarized Dark, Sepia, Sage, Rose, Dusk, and Ocean (sourced from `fountain-publisher/beta/src/branding/writeShapeThemes.ts`). Board categories use stable colored outlines around each card; there are no category dots, drop shadows, or glow effects.

## Dates, activity history, and database location

Each thought may have an optional **Due date** (an actual deadline) and separately **Bring to attention** (when Tend should nudge you). Only the attention date directly schedules a desktop notification. A due date does not imply one.

The board includes an activity timeline. Log progress, feedback, blockers or decisions with the time they happened (default: now). The AI and MCP tools also support backdated events and period reports for weeks, months, quarters and years. Reports use the recorded occurrence time, not entry time.

In **Settings → Database location**, choose either **Move current database** to a new unused SQLite filename or **Use an existing Tend database**. Both are staged until you stop and restart `tend`. A move uses SQLite backup and integrity verification and keeps the original. Using an existing database validates its schema and integrity without overwriting it. Choose a local disk or a backup-managed folder, **not a cloud-sync folder that modifies the live SQLite file while Tend is running**. The browser cannot provide a reliable native system file path through ordinary web file pickers, so paste a full path (e.g. `D:\\Backups\\Tend\\tend.sqlite3`). External `TEND_DB` environment overrides take precedence and disable Settings relocation.

## Moving the database from Settings

Open **Settings → Database location → Move current database → Browse…**. Tend opens a native folder picker on the computer running the local server. Choose an existing folder, then click **Move database**. The single `tend` launcher stops the web, MCP, and notification processes, copies and verifies the live SQLite database, switches the active database path, and restarts the services automatically. The original database stays at its previous location as a safety backup. The browser may briefly lose the connection during this operation. Do not terminate Tend during the move.

The other option, **Use an existing Tend database**, accepts an existing full database filename and validates it before switching. Database relocation is available when launched through the `tend` command; starting only `uvicorn` bypasses the supervisor that handles automatic restarts. A desktop folder chooser requires an active GUI session on the local host. Backing up the live database should be done via Tend's SQLite backup feature rather than direct file synchronization.

## Windows desktop app shortcut

Tend can run as a dedicated desktop-style browser window rather than a normal tab. In the cloned repository, first install the editable package into the virtual environment:

```powershell
.\.venv\Scripts\python.exe -m pip install -e .
powershell -ExecutionPolicy Bypass -File .\install-desktop.ps1
```

This adds a **Tend** shortcut to your Windows Desktop. Double-click it to:
1. Check `http://127.0.0.1:8765/api/health` for the Tend signature.
2. Start the local web, MCP, and reminder servers **only if Tend is not already running**.
3. Wait until the web server responds, then open Tend in an Edge/Chrome `--app` window (without a normal browser tab or toolbar).

You can also use your browser's **Install app** option thanks to `manifest.webmanifest`, but a browser-installed web-app icon **cannot start Python servers on its own**. Use the Windows **Tend** shortcut above as the reliable one-click launcher.

Tend runs locally on loopback only. The new shortcut launches a detached local server that persists after you close the window, so desktop reminders can continue while the process is running. End the Tend processes or restart Windows to stop it; an explicit tray stop control is not implemented yet. Startup issues are logged in `~/.tend/server.log` or `~/.tend/desktop-launch.log`.
