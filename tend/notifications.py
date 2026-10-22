"""Separate local notification worker; no AI calls and no browser dependence."""
import time
from . import store

def run():
    store.init()
    print("Tend desktop reminder worker running",flush=True)
    while True:
        for reminder in store.claim_notifications():
            try:
                from plyer import notification
                notification.notify(title="Tend · Time to revisit",message=reminder["title"][:220],
                                    app_name="Tend",timeout=12)
            except Exception as exc:
                # Remain alive even when OS notification integration is unavailable.
                print("Desktop notification unavailable:",type(exc).__name__,flush=True)
        time.sleep(20)

if __name__=="__main__":run()
