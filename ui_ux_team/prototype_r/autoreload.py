#!/usr/bin/env python3
import os
import sys
import subprocess
import time
import signal
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# to run
# QT_QPA_PLATFORM=xcb python3 autoreload.py py_learn.py 

WATCH_EXT = (".py",)
DEBOUNCE_DELAY = 0.3

class ReloadHandler(FileSystemEventHandler):
    def __init__(self, runner):
        super().__init__()
        self.runner = runner
        self.last_change = 0

    def on_modified(self, event):
        if event.is_directory:
            return
        if not event.src_path.endswith(WATCH_EXT):
            return

        now = time.time()
        if now - self.last_change < DEBOUNCE_DELAY:
            return
        self.last_change = now

        print(f"↻ Detected change in: {event.src_path}")
        self.runner.restart_child()


class Runner:
    def __init__(self, script_path):
        self.script = script_path
        self.proc = None

    def start_child(self):
        print("▶ Starting app…")
        self.proc = subprocess.Popen([sys.executable, self.script])

    def stop_child(self):
        if self.proc and self.proc.poll() is None:
            print("■ Stopping app…")
            self.proc.terminate()
            try:
                self.proc.wait(timeout=1)
            except subprocess.TimeoutExpired:
                self.proc.kill()

    def restart_child(self):
        self.stop_child()
        self.start_child()

    def run(self):
        self.start_child()
        try:
            while True:
                time.sleep(0.2)
                if self.proc.poll() is not None:
                    print("■ App exited.")
                    break
        except KeyboardInterrupt:
            self.stop_child()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: autoreload.py your_app.py")
        sys.exit(1)

    app_script = sys.argv[1]
    runner = Runner(app_script)

    handler = ReloadHandler(runner)
    observer = Observer()
    observer.schedule(handler, path=os.path.dirname(app_script) or ".", recursive=True)
    observer.start()

    try:
        runner.run()
    finally:
        observer.stop()
        observer.join()
