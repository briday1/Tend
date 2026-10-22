"""Persist database location and stage safe migrations for next Tend restart."""
import json, os, sqlite3
from pathlib import Path

def config_path():
    return Path.home()/".tend"/"storage.json"

def load():
    try:return json.loads(config_path().read_text(encoding="utf-8"))
    except (FileNotFoundError,ValueError):return {}

def active_path():
    return Path(load().get("active",str(Path.home()/".tend"/"tend.sqlite3"))).expanduser().resolve()

def info():
    c=load()
    return {"current":str(active_path()),"pending":c.get("pending"),"environment_override":bool(os.environ.get("TEND_DB"))}

def _write(config):
    f=config_path();f.parent.mkdir(parents=True,exist_ok=True)
    import tempfile
    fd,temp=tempfile.mkstemp(prefix=".storage-",dir=f.parent)
    try:
        with os.fdopen(fd,"w",encoding="utf-8") as stream:json.dump(config,stream)
        os.replace(temp,f)
    finally:
        if os.path.exists(temp):os.unlink(temp)

def stage(target):
    if os.environ.get("TEND_DB"):raise ValueError("Remove TEND_DB environment override before relocating the database")
    path=Path(target).expanduser().resolve()
    if path.suffix.lower() not in (".sqlite3",".sqlite",".db"):raise ValueError("Use a .sqlite3, .sqlite, or .db filename")
    if path==active_path():raise ValueError("Choose a different destination")
    if path.exists():raise ValueError("Destination exists; choose an unused file to avoid overwriting data")
    if not path.parent.is_dir():raise ValueError("Destination folder must already exist")
    if not os.access(path.parent,os.W_OK):raise ValueError("Destination folder is not writable")
    config=load();config["pending"]=str(path);_write(config)
    return info()

def activate_pending():
    """Called only by the single-command launcher before any server is started."""
    config=load();target=config.get("pending")
    if not target:return
    destination=Path(target)
    source=active_path()
    if destination.exists():raise RuntimeError("Pending database destination already exists; migration cancelled")
    destination.parent.mkdir(parents=True,exist_ok=True)
    try:
        with sqlite3.connect(source) as src,sqlite3.connect(destination) as dst:
            src.backup(dst)
            ok=dst.execute("PRAGMA integrity_check").fetchone()[0]
            if ok!="ok":raise RuntimeError("Database verification failed")
        config["active"]=str(destination);config.pop("pending",None);_write(config)
    except Exception:
        destination.unlink(missing_ok=True)
        raise
    # Source is retained as a backup, never deleted.
