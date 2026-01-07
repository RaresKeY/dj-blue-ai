import threading
import time
from typing import Optional, Callable, Dict, Any

from architects.helpers.audio_utils import (
    AudioController, 
    SoundPacketBuilder, 
    pcm_to_wav_bytes
)
from architects.helpers.api_utils import LLMUtilitySuite

class TranscriptionManager:
    """
    Manages audio recording, processing, and transcription via LLM API.
    Decouples functional logic from the UI.
    """
    def __init__(self, api_key: str, chunk_seconds: int = 30):
        if not api_key:
            raise ValueError("API Key is required for TranscriptionManager")
            
        self._llm_utils = LLMUtilitySuite(api_key)
        self._recorder: Optional[AudioController] = None
        self._is_recording = False
        self._callback: Optional[Callable[[str], None]] = None
        
        self._chunk_seconds = chunk_seconds
        self._worker_thread: Optional[threading.Thread] = None

    def set_callback(self, callback: Callable[[Dict[str, Any]], None]):
        """
        Sets the callback function to receive the raw transcription dictionary.
        Expected keys: 'text', 'summary', 'emotion', 'translation'.
        """
        self._callback = callback

    def start_recording(self):
        """Starts the audio controller and the transcription worker thread."""
        if self._recorder is not None:
            return  # Already recording

        print('[TranscriptionManager] Starting recording...')
        self._recorder = AudioController(chunk_seconds=self._chunk_seconds)
        self._recorder.start()
        
        self._is_recording = True
        self._worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
        self._worker_thread.start()

    def stop_recording(self):
        """Stops the audio controller and worker thread."""
        if self._recorder is None:
            return

        print('[TranscriptionManager] Stopping recording...')
        self._is_recording = False
        self._recorder.stop()
        self._recorder.close()
        self._recorder = None
        
        if self._worker_thread:
            # Thread will exit naturally as _is_recording is False
            self._worker_thread = None

    def is_recording(self) -> bool:
        return self._recorder is not None

    def _worker_loop(self):
        """Background loop to process audio chunks and call API."""
        while self._is_recording and self._recorder:
            if self._recorder.chunks:
                print("[TranscriptionManager] Sending audio to transcription API...")
                audio_bytes = self._recorder.pop_combined_stereo()
                
                if audio_bytes:
                    self._process_chunk(audio_bytes)
                else:
                    print("[TranscriptionManager] Pop returned None (no audio)")

            time.sleep(1)

    def _process_chunk(self, audio_bytes: bytes):
        """Processes a single audio chunk."""
        # Validate recorder state again just in case
        if not self._recorder: 
            return

        # Prepare WAV for API
        wav_bytes = pcm_to_wav_bytes(
            audio_bytes,
            rate=self._recorder.mic.rate,
            channels=2,
            sampwidth=self._recorder.mic.sampwidth
        )

        # Optional: Packet builder logic (preserved from original code)
        packet = SoundPacketBuilder(
            audio_bytes,
            rate=self._recorder.mic.rate,
            channels=2,
            sampwidth=self._recorder.mic.sampwidth
        )
        compressed_bytes = packet.prep_pck()
        print(f"[TranscriptionManager] Compressed audio prepared ({len(compressed_bytes)} bytes)")

        # Call API
        try:
            result = self._llm_utils.transcribe_audio_bytes(
                wav_bytes,
                mime_type="audio/wav",
                model_name="models/gemini-2.5-flash",
                structured=True,
            )
            
            # Cleanup result
            result.pop("raw_response", None)
            result.pop("source", None)
            result.pop("model", None)
            
            print("--- DEBUG TRANSCRIPT")
            print(result)
            print("-------- END -------\n")

            if self._callback:
                self._callback(result)

        except Exception as e:
            print(f"[TranscriptionManager] Error during transcription: {e}")

    @staticmethod
    def format_transcript_text(result: Dict[str, Any]) -> Optional[str]:
        """Formats the API result dict into a displayable string."""
        if not result.get("text"):
            return None

        def parse_none(txt):
            return txt if isinstance(txt, str) else "MISSING"

        return (
            "Transcript:\n" + parse_none(result.get("text")) + '\n\n' +
            "Translation:\n" + parse_none(result.get("translation", "MISSING")) + '\n\n' +
            "Summary:\n" + parse_none(result.get("summary", "MISSING")) + '\n\n' +
            "Emotion: " + parse_none(result.get("emotion", "MISSING")) + '\n' + "---\n"
        )
