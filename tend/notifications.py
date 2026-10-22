"""Separate local notification worker; no AI calls and no browser dependence."""
import time
from . import store, nudges

def run():
    store.init()
    print("Tend desktop reminder worker running",flush=True)
    next_nudge_check=0.0
    while True:
        for reminder in store.claim_notifications():
            try:
                from plyer import notification
                notification.notify(title="Tend · Time to revisit",message=reminder["title"][:220],
                                    app_name="Tend",timeout=12)
            except Exception as exc:
                # Remain alive even when OS notification integration is unavailable.
                print("Desktop notification unavailable:",type(exc).__name__,flush=True)
        if time.monotonic()>=next_nudge_check:
            next_nudge_check=time.monotonic()+1800
            try:
                chosen=nudges.pick()
                if chosen:
                    from plyer import notification
                    notification.notify(title="Tend · Worth revisiting",
                        message=(chosen["title"]+" — "+chosen["reason"])[:220],
                        app_name="Tend",timeout=12)
            except Exception as exc:
                print("Proactive notification unavailable:",type(exc).__name__,flush=True)
        time.sleep(20)

if __name__=="__main__":run()
