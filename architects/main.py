"""
Headless runner that wires the recording worker to the transcriber.

It discovers the best-guess capture devices, starts `RecordingWorker`
inside a Qt event loop, and forwards the generated WAV files to
`WhisperEngine` for transcription.
"""

from __future__ import annotations

import signal
import sys
import threading
from pathlib import Path
from typing import Optional
from PyQt6.QtCore import QCoreApplication

# Ensure project root is importable when running the script directly.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from the_listeners import RECORD_SECONDS, RecordingWorker, suppress_alsa_warnings
from the_listeners.device_helpers import resolve_device_params, list_all_devices
from transcribers import WhisperEngine


def _print_devices(devices) -> None:
    print("Detected audio devices:")
    if not devices:
        print("  (none)")
        return

    for dev in devices:
        name = dev.get("name", "")
        inputs = dev.get("max_input_channels", 0)
        outputs = dev.get("max_output_channels", 0)
        host_api = dev.get("host_api", -1)
        print(f"  [{dev['index']}] {name} (inputs={inputs}, outputs={outputs}, host_api={host_api})")


def _print_selection(params) -> None:
    print("Selected devices:")
    print(f"  Mic     -> [{params['mic_id']}] {params['mic_name']}")

    speaker_id = params.get("speaker_id")
    if speaker_id is None:
        print("  Speaker -> dezactivat (nu există dispozitiv de monitorizare disponibil)")
    else:
        speaker_name = params.get("speaker_name", "")
        print(f"  Speaker -> [{speaker_id}] {speaker_name}")

    print(f"  Duration -> {params['duration']}s per cycle")


def _wire_handlers(worker: RecordingWorker, whisper: WhisperEngine) -> None:
    worker.log_message.connect(lambda message: print(message))

    def on_finished(self_path: str, others_path: str) -> None:
        print("\nCycle complete:")
        print(f"  SELF   -> {self_path}")
        if others_path:
            print(f"  OTHERS -> {others_path}")
        else:
            print("  OTHERS -> skipped")

        # Prefer the speaker/loopback capture for transcription when available.
        transcription_target = others_path or self_path
        channel_label = "OTHERS" if others_path else "SELF"
        print(f"  TRANSCRIBE -> {channel_label}")
        _start_transcription(Path(transcription_target), whisper)

    worker.finished_cycle.connect(on_finished)


def _start_transcription(wav_path: Path, whisper: WhisperEngine) -> None:
    def _job():
        try:
            result = whisper.transcribe(wav_path)
        except Exception as exc:  # noqa: BLE001
            print(f"[Transcriber] Failed: {exc}")
            return

        print("\n[Transcriber] Transcript ready:")
        print(result.get("text", "").strip())
        print(result.get("metadata", {}))

    threading.Thread(target=_job, daemon=True).start()


def main() -> None:
    suppress_alsa_warnings() # TODO: configure dist
    app = QCoreApplication(sys.argv)

    devices = list_all_devices()
    _print_devices(devices)

    params = resolve_device_params(RECORD_SECONDS)
    _print_selection(params)

    worker = RecordingWorker(
        params["mic_id"],
        params.get("speaker_id"),
        20,
    )

    whisper = WhisperEngine()
    _wire_handlers(worker, whisper)

    def shutdown() -> None:
        if worker.isRunning():
            worker.stop()
            worker.wait()

    def handle_sigint(*_):
        print("\nStopping recorder...")
        shutdown()
        app.quit()

    signal.signal(signal.SIGINT, handle_sigint)

    worker.start()
    exit_code = app.exec()
    shutdown()
    sys.exit(exit_code)


if __name__ == "__main__":
    try:
        main()
    except RuntimeError as exc:
        print(f"Device discovery failed: {exc}", file=sys.stderr)
        sys.exit(1)
