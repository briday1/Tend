"""Generate reproducible Tend UI screenshots from an isolated demo database.

Install: python -m pip install playwright
         python -m playwright install chromium
Run:     python scripts/capture_screenshots.py

Only synthetic sample records are used. Never reads the user's Tend database.
All screenshot examples use generic Projects, Operations, and Product categories.
"""
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from datetime import date, timedelta
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "screenshots"
PORT = 18765


def make_demo(db):
    os.environ["TEND_DB"] = str(db)
    os.environ["TEND_CONFIG"] = str(db.parent / "empty-provider.json")
    from tend import store
    store.init()
    report = store.create("Weekly activity report", "Summarize recent Projects.")
    store.update(report["id"], {
        "category": "Projects", "recurrence": "weekly",
        "next_occurrence": "2027-01-08T17:00:00+00:00",
        "due_action": "activity_report",
        "action_prompt": "Summarize the week's recorded project activity.",
        "action_config": {"period": "week", "category": "Projects"},
    })
    for title, category, state in [
        ("Prepare briefing notes", "Projects", "open"),
        ("Review project milestones", "Projects", "waiting"),
        ("Renew development certificate", "Operations", "open"),
        ("Investigate dashboard bug", "Product", "open"),
        ("Update documentation", "Product", "paused"),
        ("Plan monthly review", "Operations", "open"),
    ]:
        t = store.create(title, "Sample data for screenshot testing.")
        store.update(t["id"], {"category": category, "state": state})
    store.record_activity(report["id"], "Collected updates for the reporting period.")
    archived = store.create("Completed onboarding checklist")
    store.update(archived["id"], {"category": "Operations"})
    store.archive_thread(archived["id"])
    next_monday=date.today()+timedelta(days=7-date.today().weekday())
    for title,cat,offset in [("Prepare briefing notes","Projects",0),("Investigate dashboard bug","Product",2),("Renew development certificate","Operations",4)]:
        matches=[t for t in store.list_threads() if t["title"]==title]
        if matches:store.update(matches[0]["id"],{"due_at":(next_monday+timedelta(days=offset)).isoformat()+"T12:00:00Z"})
    from tend.snapshot_intent import respond
    store.remember("user","give me my next week snapshot")
    store.remember("assistant",respond("give me my next week snapshot")["answer"])
    store.remember("user", "What needs my attention this week?")
    store.remember("assistant", "There are a few active items in **Projects** and **Operations**. The weekly activity report is scheduled, and milestone review is waiting on input.")
    return report["id"]


def wait_for_server(base, proc):
    for _ in range(120):
        if proc.poll() is not None:
            raise RuntimeError("Screenshot server exited: " + str(proc.returncode))
        try:
            with urlopen(base + "/api/health", timeout=1) as response:
                if response.status == 200:
                    return
        except OSError:
            time.sleep(0.25)
    raise RuntimeError("Screenshot server never became ready")


def main():
    from playwright.sync_api import sync_playwright

    OUT.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="tend-screenshots-") as scratch:
        scratch = Path(scratch)
        task_id = make_demo(scratch / "demo.sqlite3")
        env = os.environ.copy()
        env["TEND_DB"] = str(scratch / "demo.sqlite3")
        env["TEND_CONFIG"] = str(scratch / "empty-provider.json")
        env.pop("TEND_AI_API_KEY", None)
        server = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "tend.app:app",
             "--host", "127.0.0.1", "--port", str(PORT)],
            cwd=str(ROOT), env=env, stdout=subprocess.DEVNULL,
            stderr=subprocess.STDOUT,
        )
        base = "http://127.0.0.1:" + str(PORT)
        try:
            wait_for_server(base, server)
            with sync_playwright() as pw:
                browser = pw.chromium.launch(headless=True)
                page = browser.new_page(viewport={"width": 1440, "height": 900},
                                        device_scale_factor=2)
                # Never call a real AI provider during screenshot generation.
                page.route("**/api/attention*", lambda route: route.fulfill(
                    status=200, content_type="application/json",
                    body='{"items":[],"source":"demo"}'))
                page.goto(base + "/", wait_until="networkidle")
                page.locator(".snapshot-frame").first.wait_for()
                page.locator("#message").fill("give me my next week snapshot")
                page.locator("#composer").evaluate("(form) => form.requestSubmit()")
                page.locator(".snapshot-frame").nth(1).wait_for(timeout=15000)
                page.locator(".snapshot-frame").last.content_frame.locator(".day").first.wait_for()
                page.screenshot(path=str(OUT / "conversation.png"), full_page=True)
                week_start=date.today()+timedelta(days=7-date.today().weekday())
                week_end=week_start+timedelta(days=6)
                page.goto(base + "/snapshots?start="+week_start.isoformat()+"&end="+week_end.isoformat(), wait_until="networkidle")
                page.locator(".day").first.wait_for()
                assert page.locator("#weekdays span").all_text_contents() == ["Mon", "Tue", "Wed", "Thu", "Fri"], "Empty weekends must be hidden"
                assert page.locator(".summary, .stat, .eyebrow").count() == 0, "Snapshot must not include summary cards"
                page.screenshot(path=str(OUT / "snapshot-week.png"), full_page=True)
                month_start=week_start.replace(day=1)
                following=(month_start.replace(year=month_start.year+1,month=1)
                           if month_start.month==12 else month_start.replace(month=month_start.month+1))
                month_end=following-timedelta(days=1)
                page.goto(base + "/snapshots?start="+month_start.isoformat()+"&end="+month_end.isoformat(), wait_until="networkidle")
                page.locator(".day").first.wait_for()
                assert page.locator("#weekdays span").all_text_contents() == ["Mon", "Tue", "Wed", "Thu", "Fri"]
                page.screenshot(path=str(OUT / "snapshot-month.png"), full_page=True)
                page.goto(base + "/snapshots?start="+week_start.isoformat()+"&end="+week_end.isoformat(), wait_until="networkidle")
                with page.expect_download() as download_info:
                    page.locator("#png").click()
                assert download_info.value.suggested_filename.endswith(".png")
                page.goto(base + "/board", wait_until="networkidle")
                page.locator(".task-row").first.wait_for()
                page.screenshot(path=str(OUT / "tasks.png"), full_page=True)
                page.locator(".task-row").filter(has_text="Weekly activity report").click()
                page.locator("#panel:not(.hidden)").wait_for()
                page.screenshot(path=str(OUT / "task-details.png"), full_page=True)
                page.locator("#close").click()
                page.locator(".archive-switch").click()
                page.screenshot(path=str(OUT / "archive.png"), full_page=True)
                browser.close()
            print("Created:", ", ".join(p.name for p in sorted(OUT.glob("*.png"))))
        finally:
            server.terminate()
            try:
                server.wait(timeout=5)
            except subprocess.TimeoutExpired:
                server.kill()
                server.wait()


if __name__ == "__main__":
    main()
