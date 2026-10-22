"""Natural-language Tend snapshot requests must bypass AI and resolve correct ranges."""
from datetime import date
from tend.snapshot_intent import resolve

def test_next_week_full_calendar():
    assert resolve("give me my next week snapshot",date(2026,10,22))==("2026-10-26","2026-11-01")

def test_slash_and_relative_ranges():
    now=date(2026,10,22)
    assert resolve("/snapshot last month",now)==("2026-09-01","2026-09-30")
    assert resolve("/snapshot tomorrow",now)==("2026-10-23","2026-10-23")
    assert resolve("snapshot next 10 days",now)==("2026-10-22","2026-10-31")
    assert resolve("snapshot 2026-10-01 to 2026-10-22",now)==("2026-10-01","2026-10-22")
    assert resolve("What's on my mind?",now) is None
