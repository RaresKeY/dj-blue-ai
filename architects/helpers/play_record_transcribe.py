import os
from pathlib import Path
import time

from audio_utils import (
    AudioController,
    SoundPacketBuilder,
    write_wav,
)
from api_utils import LLMUtilitySuite

from dotenv import load_dotenv
load_dotenv()


def _collect_combined_chunks(controller: AudioController) -> bytes:
    combined_chunks = []
    while True:
        combined = controller.pop_combined_dual()
        if combined is None:
            break
        combined_chunks.append(combined)
    return b"".join(combined_chunks)


def main():
    api_key = os.getenv("AI_STUDIO_API_KEY")

    recorder = AudioController(chunk_seconds=30)
    recording_seconds = 30

    try:
        print(f"Recording mic + speaker for {recording_seconds} seconds...")
        recorder.start()
        time.sleep(recording_seconds)
        recorder.stop()
    finally:
        recorder.close()

    captured = _collect_combined_chunks(recorder)
    if not captured:
        raise SystemExit("No audio captured from mic + speaker.")

    recorded_wav = Path(__file__).with_name("captured_mic_speaker.wav")
    write_wav(
        str(recorded_wav),
        captured,
        rate=recorder.mic.rate,
        channels=2,
        sampwidth=recorder.mic.sampwidth,
    )

    packet = SoundPacketBuilder(
        captured,
        rate=recorder.mic.rate,
        channels=2,
        sampwidth=recorder.mic.sampwidth,
    )
    compressed_bytes = packet.prep_pck()
    compressed_path = Path(__file__).with_name("captured_mic_speaker.ulaw")
    packet.write(str(compressed_path))

    llm = LLMUtilitySuite(api_key)
    transcription = llm.transcribe_audio(
        recorded_wav,
        mime_type="audio/wav",
        model_name="models/gemini-2.5-flash",
    )

    print(f"Transcription text:\n{transcription.get('text')}")
    if transcription.get("summary"):
        print(f"Summary: {transcription.get('summary')}")
    if transcription.get("emotion"):
        print(f"Detected emotion: {transcription.get('emotion')}")

    print(f"Compressed audio saved to {compressed_path} ({len(compressed_bytes)} bytes)")


if __name__ == "__main__":
    main()
