---
name: tend-snapshot
description: Create factual, attractive Tend calendar snapshots and task activity reports for natural-language time ranges using Tend's local MCP tools.
---
# Tend /snapshot

Use when a user types `/snapshot` with or without parameters, or asks for a visual task report such as "show how last week went", "give me a colorful view of November", "what is coming up over the next two weeks", or "show WriteShape's activity from the 3rd through the 18th."

## Natural-language interpretation
- Parse relative dates using the **user's local current date and timezone**, not the model's training date or UTC. Interpret "today", "yesterday", "tomorrow", "this/last/next week", "this/last/next month", "the past N days", "next N weeks", quarters, explicit dates, and "from X through Y". Inclusive `YYYY-MM-DD` endpoints.
- Weeks start Monday unless an explicit user preference is available. For "past N days", include today; for "next N days", include today unless the user says "starting tomorrow". If user says "last week", use the preceding full Monday–Sunday week, not a rolling seven days.
- If the period is omitted, default to current week. Only ask when a genuinely unresolved ambiguity would materially change the report. For ranges longer than the server's 366-day limit, explain the limit and offer adjacent reports; never silently truncate.
- Extract any specific category only if intended as a category filter; do not mistake task names for categories. Use the `categories` MCP tool when uncertain; no fabricated category names.
- Follow explicit filters and details such as "completed", "due", "activity", "overdue" when supported; say clearly when the source data cannot support the requested historical metric. Do not hallucinate completed work based on current task statuses.
- Choose day/week/month/custom view appropriate to the date range and user request. Favor the standardized beautiful calendar visualization with active Tend theme, readable category colors and real insights. Never substitute a generative AI image for the deterministic Tend output.

## Retrieve and display
1. Invoke Tend MCP `get_snapshot(start, end, category="")` using exact inclusive ISO dates. Treat returned `days`, `insights`, and `notice` as the authoritative task data. For individual task details call `explore_thread(thread_id)`; obtain stable clickable references with `task_link(thread_id)`.
2. Return a concise prose summary grounded in the structured output: scheduled due, activity events, active days, and category distribution. Differentiate upcoming obligations from observed historical events. Cite task titles and dates only from returned records, never invent activity, effort, productivity scores, status histories, or due dates.
3. Present an interactive rich view if the host supports it. In Tend, use the `/snapshots` page and its calendar/task drawer; link to task records using the MCP-provided `/board#task/<id>` link (on the local Tend origin). In other MCP clients, render ordinary links if available. Do not promise that a third-party host can open Tend's in-app drawer.
4. For PNG export, use the local Tend `/api/snapshot.png?start=YYYY-MM-DD&end=YYYY-MM-DD&theme=THEME&scale=2` route or Tend's PNG export control. Supported scales: 1, 2, 4. SVG export is available in Tend's snapshot interface. Never report a file exported unless it was actually created or returned by the integration.
5. Default to current Tend theme when rendering in the app. When a remote MCP client cannot obtain the user's theme, do not pretend it did; use a disclosed default or ask when materially important.
6. For empty periods, show a tasteful empty calendar and zero counts, not fabricated example tasks. Distinguish recorded activity from current due dates using Tend's `notice`.

## Example prompts
- `/snapshot`
- `/snapshot yesterday`
- `/snapshot how did last week go?`
- `/snapshot show October and highlight activity from WriteShape`
- `/snapshot next two weeks, show what is coming due`
- `/snapshot between September 15 and October 20, in Ocean theme`
- `/snapshot last month as PNG at 4x`
- `/snapshot what changed this quarter for Cork?`
