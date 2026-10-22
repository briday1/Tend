"""Snapshot data and PNG export behavior; runs against isolated SQLite."""
import io
from datetime import date, timedelta
from PIL import Image
from tend import store
from tend.snapshots import snapshot
from tend.snapshot_export import png

def test_snapshot_actual_records(tmp_path,monkeypatch):
    monkeypatch.setenv("TEND_DB",str(tmp_path/"test.sqlite3"))
    store.init()
    t=store.create("Finish interactive snapshots")
    store.update(t["id"],{"category":"Product","due_at":"2026-10-24T12:00:00Z"})
    store.record_activity(t["id"],"Started visualization","progress","2026-10-23T10:00:00Z")
    report=snapshot("2026-10-22","2026-10-25")
    assert report["insights"]["scheduled_due"]==1
    assert report["insights"]["activity_events"]==1
    assert report["insights"]["active_days"]==1
    assert report["days"][2]["tasks"][0]["href"]=="/board#task/"+t["id"]
    assert report["days"][1]["activity"][0]["body"]=="Started visualization"
    assert "historical" in report["notice"].lower()
    result=png("2026-10-22","2026-10-25",theme="ocean",scale=2)
    image=Image.open(io.BytesIO(result))
    assert image.format=="PNG"
    assert image.width==2380 and image.height>600
    assert png("2026-10-22","2026-10-25",theme="ocean",scale=2)==result

def test_range_validation(tmp_path,monkeypatch):
    import pytest
    monkeypatch.setenv("TEND_DB",str(tmp_path/"test.sqlite3"))
    store.init()
    with pytest.raises(ValueError):
        snapshot("2026-11-01","2026-10-01")
    with pytest.raises(ValueError):
        snapshot("2026-01-01","2028-01-01")
    with pytest.raises(ValueError):
        png("2026-10-01","2026-10-02",theme="invalid")
