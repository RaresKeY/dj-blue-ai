import argparse
import signal
import subprocess
import sys
import time
from pathlib import Path

TARGET_TO_FILE = {
    "main": "preview_main_window.py",
    "chat": "preview_chat_window.py",
    "transcript": "preview_transcript_window.py",
    "widgets": "preview_widgets.py",
    "volume": "preview_volume.py",
    "theme": "preview_theme_chooser.py",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run a blue_ui preview and auto-restart when that preview file changes."
    )
    parser.add_argument(
        "target",
        choices=sorted(TARGET_TO_FILE.keys()),
        help="Preview target to run.",
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=0.6,
        help="Polling interval in seconds (default: 0.6).",
    )
    return parser.parse_args()


def start_child(preview_file: Path) -> subprocess.Popen:
    print(f"[preview] starting: {preview_file}")
    return subprocess.Popen([sys.executable, str(preview_file)])


def stop_child(proc: subprocess.Popen | None) -> None:
    if proc is None:
        return
    if proc.poll() is not None:
        return

    proc.terminate()
    try:
        proc.wait(timeout=3)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait(timeout=3)


def main() -> int:
    args = parse_args()
    preview_dir = Path(__file__).resolve().parent
    preview_file = preview_dir / TARGET_TO_FILE[args.target]

    if not preview_file.exists():
        print(f"[preview] missing file: {preview_file}", file=sys.stderr)
        return 1

    last_mtime = preview_file.stat().st_mtime
    child = start_child(preview_file)

    def handle_stop(*_):
        stop_child(child)
        raise SystemExit(0)

    signal.signal(signal.SIGINT, handle_stop)
    signal.signal(signal.SIGTERM, handle_stop)

    try:
        while True:
            time.sleep(args.interval)

            if child.poll() is not None:
                # If app closed manually, start it again only after a file change.
                pass

            try:
                current_mtime = preview_file.stat().st_mtime
            except FileNotFoundError:
                continue

            if current_mtime != last_mtime:
                last_mtime = current_mtime
                print(f"[preview] change detected: {preview_file.name}, restarting")
                stop_child(child)
                child = start_child(preview_file)
    except KeyboardInterrupt:
        pass
    finally:
        stop_child(child)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
