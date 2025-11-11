from __future__ import annotations

import sys

from the_listeners import RECORD_SECONDS, RecordingWorker
from the_listeners.device_helpers import resolve_device_params
from transcribers import WhisperEngine


def main() -> None:
    params = resolve_device_params(RECORD_SECONDS)

    print("Selected devices:")
    print(f"  Mic     -> [{params['mic_id']}] {params['mic_name']}")
    print(f"  Speaker -> [{params['speaker_id']}] {params['speaker_name']}")
    print(f"  Duration -> {params['duration']}s per cycle")

    # records microphone OR speakers
    listener_worker = RecordingWorker(
        params["mic_id"],
        params["speaker_id"],
        params["duration"],
    )
    listener_worker.start()

    # local whisper model (TODO: manage cpu usage)
    transcriber_worker = WhisperEngine()

    last_path = listener_worker.finished_cycle

    while True:
        if listener_worker.finished_cycle is not last_path:
            data = transcriber_worker.transcribe(listener_worker.finished_cycle)
            print(data["text"])
            # print(data["segments"])
            print(data["metadata"])

        last_path = listener_worker.finished_cycle

        data["text"]

if __name__ == "__main__":
    try:
        main()
    except RuntimeError as exc:
        print(f"Device discovery failed: {exc}", file=sys.stderr)
        sys.exit(1)

    
