import os
import time
from io import BytesIO
import wave

from audio_utils import AudioController, SoundPacketBuilder
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


def _pcm_to_wav_bytes(pcm: bytes, *, rate: int, channels: int, sampwidth: int) -> bytes:
    buf = BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(sampwidth)
        wf.setframerate(rate)
        wf.writeframes(pcm)
    return buf.getvalue()


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

    packet = SoundPacketBuilder(
        captured,
        rate=recorder.mic.rate,
        channels=2,
        sampwidth=recorder.mic.sampwidth,
    )
    compressed_bytes = packet.prep_pck()

    llm = LLMUtilitySuite(api_key)
    wav_bytes = _pcm_to_wav_bytes(
        captured,
        rate=recorder.mic.rate,
        channels=2,
        sampwidth=recorder.mic.sampwidth,
    )
    transcription = llm.transcribe_audio_bytes(
        wav_bytes,
        mime_type="audio/wav",
        model_name="models/gemini-2.5-flash-lite",
    )

    print(f"Transcription text:\n{transcription.get('text')}")
    if transcription.get("summary"):
        print(f"Summary: {transcription.get('summary')}")
    if transcription.get("emotion"):
        print(f"Detected emotion: {transcription.get('emotion')}")

    print(f"Compressed audio prepared ({len(compressed_bytes)} bytes, not saved to disk)")


if __name__ == "__main__":
    main()
