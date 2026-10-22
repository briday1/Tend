"""Windows desktop entry point: start Tend only when needed, then open an app window."""
import json
import os
import subprocess
import sys
import time
import webbrowser
from pathlib import Path
from urllib.request import urlopen
from urllib.error import URLError

def log(message):
    path=Path.home()/".tend"/"desktop-launch.log"
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open("a",encoding="utf-8") as f:f.write(message+"\n")

def port():
    return int(os.environ.get("TEND_WEB_PORT","8765"))

def healthy():
    try:
        with urlopen(f"http://127.0.0.1:{port()}/api/health",timeout=0.75) as response:
            data=json.load(response)
            return response.status==200 and data.get("app")=="tend"
    except (OSError,ValueError,URLError):
        return False

def open_app():
    url=f"http://127.0.0.1:{port()}/"
    paths=[]
    for root in (os.environ.get("PROGRAMFILES(X86)",""),os.environ.get("PROGRAMFILES",""),os.environ.get("LOCALAPPDATA","")):
        if root:
            paths.extend([str(Path(root)/"Microsoft"/"Edge"/"Application"/"msedge.exe"),
                          str(Path(root)/"Google"/"Chrome"/"Application"/"chrome.exe")])
    for executable in paths:
        if Path(executable).is_file():
            subprocess.Popen([executable,"--app="+url],close_fds=True)
            return
    webbrowser.open(url)

def main():
    if sys.platform!="win32":
        raise SystemExit("Desktop launcher currently supports Windows.")
    if not healthy():
        py=sys.executable
        if py.lower().endswith("pythonw.exe"):
            py=py[:-len("pythonw.exe")]+"python.exe"
        flags=getattr(subprocess,"CREATE_NO_WINDOW",0)|getattr(subprocess,"DETACHED_PROCESS",0)
        env=os.environ.copy()
        env["TEND_NO_BROWSER"]="1"
        logs=Path.home()/".tend"/"server.log"
        logs.parent.mkdir(parents=True,exist_ok=True)
        with logs.open("ab") as output:
            child=subprocess.Popen([py,"-m","tend.cli"],env=env,creationflags=flags,
                             stdin=subprocess.DEVNULL,stdout=output,stderr=subprocess.STDOUT,
                             close_fds=True)
        for _ in range(120):
            if healthy():break
            if child.poll() is not None:
                raise RuntimeError("Tend server process exited. Check ~/.tend/server.log")
            time.sleep(.25)
        else:
            log("Tend server failed to become ready; see server.log")
            raise RuntimeError("Tend did not start; see ~/.tend/server.log")
    open_app()

if __name__=="__main__":
    try:main()
    except Exception as exc:
        log(type(exc).__name__+": "+str(exc))
        raise
