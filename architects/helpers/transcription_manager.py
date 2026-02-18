import threading
import time
from typing import Optional, Callable, Dict, Any, List

import tempfile
import os
from architects.helpers.audio_utils import (
    AudioController, 
    LiveMixerController,
    SoundPacketBuilder, 
    pcm_to_wav_bytes
)
from architects.helpers.api_utils import LLMUtilitySuite
from mood_readers.librosa_cli import analyze_audio_bytes_logic
from architects.platform_detection.platform_detection import os_info

class TranscriptionManager:
    """
    Manages audio recording, processing, and transcription via LLM API.
    Decouples functional logic from the UI.
    """
    def __init__(self, api_key: str, chunk_seconds: int = 30, blacklist: Optional[List[str]] = None):
        if not api_key:
            raise ValueError("API Key is required for TranscriptionManager")
            
        self._llm_utils = LLMUtilitySuite(api_key)
        self._recorder: Optional[Any] = None
        self._is_recording = False
        self._callback: Optional[Callable[[str], None]] = None
        
        self._chunk_seconds = chunk_seconds
        
        # Use the blacklist provided by the user
        self._blacklist = blacklist or ['pw-record', 'live-mixer', 'easyeffects', 'loopback', 'speech-dispatcher', 'python']
        
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

        # Detect platform
        info = os_info()
        if info.get("system") == "Linux":
            print('[TranscriptionManager] Linux detected, using LiveMixerController')
            self._recorder = LiveMixerController(
                chunk_seconds=self._chunk_seconds,
                blacklist=self._blacklist
            )
        else:
            print(f'[TranscriptionManager] {info.get("system")} detected, using AudioController')
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
            # Check if there are chunks to process
            audio_bytes = self._recorder.pop_combined_stereo()
            
            if audio_bytes:
                print("[TranscriptionManager] Sending audio to transcription API...")
                self._process_chunk(audio_bytes)
            else:
                # print("[TranscriptionManager] No audio chunk ready")
                pass

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

        # In-memory Librosa analysis
        analysis_tags = ""
        try:
            analysis = analyze_audio_bytes_logic(wav_bytes)
            bpm = analysis.get("bpm", "N/A")
            camelot = analysis.get("key_camelot", "N/A")
            mood = analysis.get("mood_detailed", "N/A")
            analysis_tags = f"[Audio Analysis: {bpm} BPM, Camelot Key: {camelot}, Mood: {mood}]"
            print(f"[TranscriptionManager] Librosa Analysis: {analysis_tags}")
        except Exception as e:
            print(f"[TranscriptionManager] Librosa analysis failed: {e}")

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
            prompt = None
            if analysis_tags:
                from architects.helpers.api_utils import CUSTOM_TRANSCRIPTION_PROMPT_MEET_TYPE_SIMPLE
                prompt = f"{analysis_tags}\n\n{CUSTOM_TRANSCRIPTION_PROMPT_MEET_TYPE_SIMPLE}"

            result = self._llm_utils.transcribe_audio_bytes(
                wav_bytes,
                mime_type="audio/wav",
                model_name="models/gemini-2.5-flash-lite",
                prompt=prompt,
                structured=True,
            )

            if result.get("error"):
                print(f"[TranscriptionManager] API error: {result.get('error')}")
                if self._callback:
                    self._callback(result)
                if result.get("limit_blocked"):
                    # Stop loop to prevent repeated rate-limit spam.
                    self.stop_recording()
                return
            
            # Cleanup result
            result.pop("raw_response", None)
            result.pop("source", None)
            result.pop("model", None)
            
            # Add analysis to result for callback
            if analysis_tags:
                result["audio_analysis"] = analysis_tags

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
