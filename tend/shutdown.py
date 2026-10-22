"""Windows-safe shutdown of an owned Tend supervisor and all its subprocesses."""
import time
import psutil

def stop_process_tree(pid,log=print):
    """Stop deepest descendants first so orphaned uvicorn/MCP processes don't linger."""
    try:
        root=psutil.Process(pid)
        descendants=root.children(recursive=True)
    except psutil.NoSuchProcess:
        return
    # Snapshot the owned tree before terminating anything; never select unrelated python processes.
    def depth(proc):
        count=0
        try:
            parent=proc.parent()
            while parent and parent.pid!=root.pid and count<32:
                count+=1
                parent=parent.parent()
        except psutil.Error:pass
        return count
    descendants.sort(key=depth,reverse=True)
    processes=descendants+[root]
    for proc in processes:
        try:
            if proc.is_running():proc.terminate()
        except psutil.NoSuchProcess:pass
        except psutil.Error as exc:log("Terminate "+str(proc.pid)+": "+str(exc))
    _,alive=psutil.wait_procs(processes,timeout=4)
    for proc in alive:
        try:proc.kill()
        except psutil.NoSuchProcess:pass
        except psutil.Error as exc:log("Kill "+str(proc.pid)+": "+str(exc))
    psutil.wait_procs(alive,timeout=3)
    for proc in processes:
        try:
            if proc.is_running() and proc.status()!=psutil.STATUS_ZOMBIE:
                log("Tend process still running after exit: "+str(proc.pid))
        except psutil.NoSuchProcess:pass
