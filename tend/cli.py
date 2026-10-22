"""Start Tend's local browser and HTTP MCP servers with one command."""
import os
import subprocess
import sys
import time
import webbrowser
from urllib.request import urlopen
from urllib.error import URLError
from . import store

def main():
    store.init()
    env=os.environ.copy()
    web_host="127.0.0.1"
    web_port=int(env.get("TEND_WEB_PORT","8765"))
    mcp_port=int(env.get("TEND_MCP_PORT","8766"))
    if web_port==mcp_port: raise SystemExit("Web and MCP ports must differ")
    commands=[
        [sys.executable,"-m","uvicorn","tend.app:app","--host",web_host,"--port",str(web_port)],
        [sys.executable,"-m","tend.mcp_server","--http"]
    ]
    children=[]
    try:
        for command in commands:
            children.append(subprocess.Popen(command,env=env))
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
        while all(child.poll() is None for child in children):
            time.sleep(.4)
        raise RuntimeError("A Tend server stopped unexpectedly")
    except KeyboardInterrupt:
        pass
    finally:
        for child in children:
            if child.poll() is None:child.terminate()
        for child in children:
            try:child.wait(timeout=5)
            except subprocess.TimeoutExpired:child.kill()

if __name__=="__main__":main()
