"""Native Windows Tend window. Built into Tend.exe by install-desktop.ps1."""
import ctypes
import io
import os
import sys
import time
from pathlib import Path

def _existing_window():
    hwnd=ctypes.windll.user32.FindWindowW(None,"Tend")
    if hwnd:
        ctypes.windll.user32.ShowWindow(hwnd,9)
        ctypes.windll.user32.SetForegroundWindow(hwnd)
    return bool(hwnd)

def main():
    from tend import desktop
    import webview
    import pystray
    from PIL import Image
    from tend.windows_icon import raster

    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("Tend.Desktop")
    create=ctypes.windll.kernel32.CreateMutexW
    create.restype=ctypes.c_void_p
    create.argtypes=(ctypes.c_void_p,ctypes.c_int,ctypes.c_wchar_p)
    mutex=create(None,False,"Local\\TendNativeDesktop")
    if not mutex:raise RuntimeError("Could not create native Tend mutex")
    if ctypes.windll.kernel32.GetLastError()==183:
        for _ in range(20):
            if _existing_window():break
            time.sleep(.25)
        ctypes.windll.kernel32.CloseHandle(mutex)
        return

    supervisor=None
    tray=None
    exiting=False
    try:
        root=Path(sys.executable).resolve().parent.parent.parent if getattr(sys,"frozen",False) else Path(__file__).resolve().parent.parent
        py=root/".venv"/"Scripts"/"python.exe"
        if not py.is_file():
            raise RuntimeError("Tend Python environment not found: "+str(py)+". Re-run install-desktop.ps1.")
        os.environ["TEND_SERVICE_PYTHON"]=str(py)
        supervisor=desktop.start_and_open(open_window=False)
        window=webview.create_window("Tend",f"http://127.0.0.1:{desktop.port()}/",
              width=1180,height=780,min_size=(620,450),background_color="#f5f5f5",text_select=True)
        def on_close():
            if not exiting:
                window.hide()
                return False
        window.events.closing+=on_close

        def reopen(icon,item):
            try:
                window.show()
                window.restore()
            except Exception as exc:desktop.log("Native reopen failed: "+repr(exc))
        def exit_app(icon,item):
            nonlocal exiting
            exiting=True
            icon.stop()
            if supervisor is not None and supervisor.poll() is None:
                import psutil
                try:
                    parent=psutil.Process(supervisor.pid)
                    children=parent.children(recursive=True)
                    parent.terminate()
                    for child in children:child.terminate()
                    _,alive=psutil.wait_procs(children,timeout=3)
                    for child in alive:child.kill()
                except psutil.Error as exc:desktop.log("Native service shutdown: "+repr(exc))
            window.destroy()
        tray=pystray.Icon("Tend",Image.open(io.BytesIO(raster(256))).convert("RGBA"),"Tend",
             pystray.Menu(pystray.MenuItem("Open Tend",reopen,default=True),
                           pystray.MenuItem("Exit Tend",exit_app)))
        tray.run_detached()
        webview.start(gui="edgechromium")
    finally:
        if tray:
            try:tray.stop()
            except Exception:pass
        ctypes.windll.kernel32.CloseHandle(mutex)

if __name__=="__main__":
    try:main()
    except Exception as exc:
        from tend.desktop import log,show_error
        log("Native launcher: "+repr(exc))
        show_error(str(exc)+"\\n\\nSee .tend/desktop-launch.log")
        raise
