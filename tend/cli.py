"""Start Tend's local browser and HTTP MCP servers with one command."""
import os
import subprocess
import sys
import time
import webbrowser
from urllib.request import urlopen
from urllib.error import URLError
from . import store
from . import storage
from pathlib import Path

def main():
    # Detect an older Tend supervisor before opening a new browser tab.
    import socket
    with socket.socket() as probe:
        probe.settimeout(.5)
        if probe.connect_ex(("127.0.0.1",int(os.environ.get("TEND_WEB_PORT","8765"))))==0:
            raise SystemExit("Tend port is already in use. Close the previous Tend server before starting a new one. Older servers may not support /api/chat/stream.")
    store.init()
    storage.activate_pending()
    store.init()
    env=os.environ.copy()
    web_host="127.0.0.1"
    web_port=int(env.get("TEND_WEB_PORT","8765"))
    mcp_port=int(env.get("TEND_MCP_PORT","8766"))
    if web_port==mcp_port: raise SystemExit("Web and MCP ports must differ")
    commands=[
        [sys.executable,"-m","uvicorn","tend.app:app","--host",web_host,"--port",str(web_port)],
        [sys.executable,"-m","tend.mcp_server","--http"],
        [sys.executable,"-m","tend.notifications"]
    ]
    children=[]
    # On Windows, child python.exe processes otherwise create their own console.
    flags=getattr(subprocess,"CREATE_NO_WINDOW",0) if os.name=="nt" else 0
    log_path=Path.home()/".tend"/"services.log"
    log_path.parent.mkdir(parents=True,exist_ok=True)
    try:
        for command in commands:
            with log_path.open("ab") as output:
                children.append(subprocess.Popen(command,env=env,creationflags=flags,
                    stdin=subprocess.DEVNULL,stdout=output,stderr=subprocess.STDOUT,
                    close_fds=True))
        url=f"http://{web_host}:{web_port}"
        print(f"Tend browser: {url}",flush=True)
        print(f"Tend MCP: http://127.0.0.1:{mcp_port}/mcp",flush=True)
        print(f"Local database: {store.path()}",flush=True)
        print("Press Ctrl+C to stop both servers.",flush=True)
        # Wait for a valid response instead of opening an unavailable page.
        deadline=time.monotonic()+20
        ready=False
        while time.monotonic()<deadline:
            if any(child.poll() is not None for child in children):
                raise RuntimeError("Tend failed to start. See server output above.")
            try:
                with urlopen(url,timeout=0.8) as response:
                    ready=response.status==200
                if ready:break
            except (URLError,OSError,TimeoutError):
                time.sleep(.2)
        if not ready:raise RuntimeError("Tend did not become ready on "+url)
        if env.get("TEND_NO_BROWSER")!="1":
            webbrowser.open(url)
        while True:
            if any(child.poll() is not None for child in children):
                raise RuntimeError("A Tend server stopped unexpectedly")
            if storage.load().get("pending"):
                print("Switching Tend database; restarting local services...",flush=True)
                for child in children:
                    if child.poll() is None:child.terminate()
                for child in children:
                    try:child.wait(timeout=10)
                    except subprocess.TimeoutExpired:
                        child.kill()
                        child.wait()
                children.clear()
                try:
                    storage.activate_pending()
                except Exception as exc:
                    print("Database switch failed; retaining existing database:",str(exc),flush=True)
                    # Clear the pending switch to avoid repeatedly interrupting running services.
                    c=storage.load();c.pop("pending",None);c.pop("pending_mode",None);storage._write(c)
                store.init()
                for command in commands:
                    with log_path.open("ab") as output:
                        children.append(subprocess.Popen(command,env=env,creationflags=flags,
                            stdin=subprocess.DEVNULL,stdout=output,stderr=subprocess.STDOUT,
                            close_fds=True))
                deadline=time.monotonic()+20
                while time.monotonic()<deadline:
                    if any(child.poll() is not None for child in children):
                        raise RuntimeError("Tend restart failed")
                    try:
                        with urlopen(url,timeout=.8) as response:
                            if response.status==200:break
                    except (URLError,OSError,TimeoutError):
                        time.sleep(.2)
                else:raise RuntimeError("Tend web server did not restart")
                print("Tend database active:",store.path(),flush=True)
            time.sleep(.4)
    except KeyboardInterrupt:
        pass
    finally:
        for child in children:
            if child.poll() is None:child.terminate()
        for child in children:
            try:child.wait(timeout=5)
            except subprocess.TimeoutExpired:child.kill()

if __name__=="__main__":main()
