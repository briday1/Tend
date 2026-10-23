"""Native Windows Tether window. Built into Tether.exe by install-desktop.ps1."""
import ctypes
import io
import os
import sys
import time
from pathlib import Path

def _existing_window():
    ctypes.windll.user32.FindWindowW.restype=ctypes.c_void_p
    hwnd=ctypes.windll.user32.FindWindowW(None,"Tether")
    if hwnd:
        ctypes.windll.user32.ShowWindow(hwnd,9)
        ctypes.windll.user32.SetForegroundWindow(hwnd)
    return bool(hwnd)


def _apply_windows_window_icon():
    """Set both Win32 icon sizes on the real pywebview HWND, not python.exe."""
    import tempfile
    from tend.windows_icon import create_icon
    user32=ctypes.windll.user32
    icon_file=Path(tempfile.gettempdir())/"tether-horizon-window.ico"
    create_icon(icon_file)
    user32.LoadImageW.restype=ctypes.c_void_p
    user32.LoadImageW.argtypes=[ctypes.c_void_p,ctypes.c_wchar_p,ctypes.c_uint,ctypes.c_int,ctypes.c_int,ctypes.c_uint]
    user32.SendMessageW.restype=ctypes.c_ssize_t
    user32.SendMessageW.argtypes=[ctypes.c_void_p,ctypes.c_uint,ctypes.c_size_t,ctypes.c_ssize_t]
    user32.FindWindowW.restype=ctypes.c_void_p
    user32.FindWindowW.argtypes=[ctypes.c_wchar_p,ctypes.c_wchar_p]
    hwnd=user32.FindWindowW(None,"Tether")
    if not hwnd:
        desktop_error="Tether window was not found for icon assignment"
        raise RuntimeError(desktop_error)
    for size,index in ((16,0),(32,1)):
        icon=user32.LoadImageW(None,str(icon_file),1,size,size,0x10)
        if icon:user32.SendMessageW(hwnd,0x80,index,icon)

def main():
    from tend import desktop
    if sys.platform!="win32":
        server=desktop.start_and_open(open_window=True)
        try:
            desktop.run_tray(server)
        except KeyboardInterrupt:
            if server is not None and server.poll() is None:
                from tend.shutdown import stop_process_tree
                stop_process_tree(server.pid,log=desktop.log)
        return
    import webview
    import pystray
    from PIL import Image
    from tend.windows_icon import raster

    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("Tether.Desktop")
    create=ctypes.windll.kernel32.CreateMutexW
    create.restype=ctypes.c_void_p
    create.argtypes=(ctypes.c_void_p,ctypes.c_int,ctypes.c_wchar_p)
    mutex=create(None,False,"Local\\TetherNativeDesktop")
    if not mutex:raise RuntimeError("Could not create native Tether mutex")
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
        root=Path(sys.executable).resolve().parent.parent if getattr(sys,"frozen",False) else Path(__file__).resolve().parent.parent
        py=root/".venv"/"Scripts"/"python.exe"
        if not py.is_file():py=Path(sys.executable)

        os.environ["TEND_SERVICE_PYTHON"]=str(py)
        supervisor=desktop.start_and_open(open_window=False)
        window=webview.create_window("Tether",f"http://127.0.0.1:{desktop.port()}/",
              width=1180,height=780,min_size=(620,450),background_color="#f5f5f5",text_select=True)
        def on_close():
            if not exiting:
                window.hide()
                return False
        window.events.closing+=on_close
        window.events.shown+=_apply_windows_window_icon

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
                try:
                    from tend.shutdown import stop_process_tree
                    stop_process_tree(supervisor.pid,log=desktop.log)
                except Exception as exc:
                    desktop.log("Native service shutdown failed: "+repr(exc))
            try:window.destroy()
            except Exception:pass
        tray=pystray.Icon("Tether",Image.open(io.BytesIO(raster(256))).convert("RGBA"),"Tether",
             pystray.Menu(pystray.MenuItem("Open Tether",reopen,default=True),
                           pystray.MenuItem("Exit Tether",exit_app)))
        tray.run_detached()
        webview.start(gui="edgechromium",debug=False)
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
