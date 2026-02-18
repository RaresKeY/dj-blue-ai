import json
import mimetypes
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np

from architects.helpers.genai_client import GenAIClient, GenAIChatSession
from ui_ux_team.blue_ui.app.api_usage_guard import record_usage, reserve_request

MEET_TYPE_MOODS = "positive|neutral|tense|unfocused|collaborative|creative|unproductive"

CUSTOM_TRANSCRIPTION_PROMPT_MEET_TYPE = f"""
Process the audio file and generate a detailed transcription.

Requirements:
1. Detect the primary language.
2. If the recording is in a language different than English, also provide the English translation.
3. Identify the primary emotion of the speaker in this recording. You MUST choose exactly one of the following: {MEET_TYPE_MOODS}.
4. Provide a brief summary of the entire audio at the beginning.
5. Silence/Noise: If no speech is detected, set "content" to "" (empty string). Do not hallucinate text.
6. Do not use timestamps in content.

Respond ONLY as JSON matching:
{{
  "summary": "string",
  "content": "string",
  "translation": "string|None",
  "language_code": "string",
  "emotion": "{MEET_TYPE_MOODS}"
}}
""".strip()

CUSTOM_TRANSCRIPTION_PROMPT_MEET_TYPE_SIMPLE = f"""
Analyze the audio and output ONLY valid JSON.

Allowed Emotions: {MEET_TYPE_MOODS}

Instructions:
1. content: Transcribe exactly. If silent/noise only, return "". No timestamps.
2. language_code: Use 2-letter ISO code (e.g., "en", "es").
3. translation: English translation. If audio is English, return null.
4. emotion: Select exactly one from 'Allowed Emotions'.
5. do not add timestamps in response.

Required JSON Format:
{{
  "summary": "Brief summary",
  "content": "Full transcription",
  "translation": "Translation or null",
  "language_code": "en",
  "emotion": "Chosen Emotion"
}}
""".strip()

DEFAULT_TRANSCRIPTION_PROMPT = """
Process the audio file and generate a detailed transcription.

Requirements:
1. Identify distinct speakers (e.g., Speaker 1, Speaker 2, or names if context allows).
2. Provide accurate timestamps for each segment (Format: MM:SS).
3. Detect the primary language of each segment.
4. If the segment is in a language different than English, also provide the English translation.
5. Identify the primary emotion of the speaker in this segment. You MUST choose exactly one of the following: Happy, Sad, Angry, Neutral.
6. Provide a brief summary of the entire audio at the beginning.

Respond ONLY as JSON matching:
{
  "summary": "string",
  "segments": [
    {
      "speaker": "string",
      "timestamp": "MM:SS",
      "content": "string",
      "language": "string",
      "language_code": "string",
      "translation": "string",
      "emotion": "happy|sad|angry|neutral"
    }
  ]
}
""".strip()

# Gemini inline audio limit is 20 MB; larger files should be uploaded first.
INLINE_AUDIO_LIMIT_BYTES = 20 * 1024 * 1024


class LLMUtilitySuite:
    """
    A singleton class to manage interactions with a Large Language Model API.
    This suite handles API configuration, text generation (with system prompts),
    chat sessions, text embeddings, and audio transcription.
    """
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(LLMUtilitySuite, cls).__new__(cls)
        return cls._instance

    def __init__(self, api_key: str = None):
        if not hasattr(self, 'is_initialized'):
            if api_key is None:
                raise ValueError("API key is required for the first initialization.")

            try:
                self.client = GenAIClient(api_key=api_key)
                print("LLM API Suite configured successfully via GenAIClient.")
                self.is_initialized = True
            except Exception as e:
                self.is_initialized = False
                raise ConnectionError(f"Failed to configure API: {e}")

    # --- PROMPTING METHODS ---

    def generate_text(
        self,
        prompt: str,
        model_name: str = "gemini-flash-latest",
        system_prompt: str = None
    ) -> str:
        try:
            config = {"system_instruction": system_prompt} if system_prompt else None
            response = self.client.generate_content(
                model_name=self._normalize_model_name(model_name),
                contents=prompt,
                config=config
            )
            return response.get("text", "")
        except Exception as e:
            return f"An error occurred during text generation: {e}"

    def start_chat(
        self,
        model_name: str = "gemini-1.5-flash"
    ) -> GenAIChatSession:
        try:
            return GenAIChatSession(
                client=self.client.client,
                model_name=self._normalize_model_name(model_name)
            )
        except Exception as e:
            print(f"Could not start chat session: {e}")
            return None

    @staticmethod
    def send_chat_message(
        chat_session: GenAIChatSession,
        message: str
    ) -> str:
        if not chat_session:
            return "Chat session is not initialized."
        try:
            response = chat_session.send_message(message)
            return response.get("text", "")
        except Exception as e:
            return f"An error occurred during the chat: {e}"

    # --- EMBEDDING METHODS ---

    def get_embedding(
        self,
        text: str,
        model_name: str = "models/embedding-001",
        task_type: str = "RETRIEVAL_DOCUMENT"
    ) -> List[float]:
        try:
            embeddings = self.client.embed_content(
                model_name=model_name,
                contents=text
            )
            return embeddings[0] if embeddings else []
        except Exception as e:
            print(f"An error occurred during embedding: {e}")
            return []

    def get_batch_embeddings(
        self,
        texts: List[str],
        model_name: str = "models/embedding-001",
        task_type: str = "RETRIEVAL_DOCUMENT"
    ) -> List[List[float]]:
        try:
            return self.client.embed_content(
                model_name=model_name,
                contents=texts
            )
        except Exception as e:
            print(f"An error occurred during batch embedding: {e}")
            return []

    # --- TRANSCRIPTION METHODS ---

    def transcribe_audio(
        self,
        audio_source: Union[str, Path, bytes],
        *,
        model_name: str = "models/gemini-2.5-flash-lite",
        prompt: Optional[str] = None,
        mime_type: Optional[str] = None,
        structured: bool = True,
        upload_when_large: bool = True,
        upload_threshold_bytes: int = INLINE_AUDIO_LIMIT_BYTES,
        wait_for_active_sec: int = 60,
    ) -> Dict[str, Any]:
        allowed, reason = reserve_request("transcript", model_name=model_name)
        if not allowed:
            return {
                "error": reason,
                "limit_blocked": True,
                "source": "api_usage_limits",
                "model": model_name,
            }

        prompt = prompt or CUSTOM_TRANSCRIPTION_PROMPT_MEET_TYPE
        audio_part, source = self._prepare_audio_part(
            audio_source,
            mime_type=mime_type,
            upload_when_large=upload_when_large,
            upload_threshold_bytes=upload_threshold_bytes,
        )

        config = {}
        if structured:
            config["response_mime_type"] = "application/json"
            # Schema passing in google.genai differs; keeping simple JSON prompt for now
            # as defined in the migration plan's risk mitigation section.

        try:
            normalized_model = self._normalize_model_name(model_name)
            response = self.client.generate_content(
                model_name=normalized_model,
                contents=[prompt, audio_part],
                config=config if config else None
            )
            usage = response.get("usage", {})
            self._log_usage_dict(usage, context="transcribe_audio")
            record_usage(scope="transcript", model_name=normalized_model, usage=usage)
        except Exception as e:
            return {
                "error": f"An error occurred during transcription: {e}",
                "source": source,
                "model": model_name,
            }

        parsed = self._maybe_parse_structured_json(response.get("text", ""), structured)
        transcript_text = parsed.get("content") if parsed else response.get("text", "")
        primary_emotion = parsed.get("emotion") if parsed else None

        return {
            "text": (transcript_text or "").strip(),
            "summary": parsed.get("summary") if parsed else None,
            "emotion": primary_emotion,
            "raw_response": response.get("raw_response"),
            "source": source,
            "model": model_name,
            "translation": parsed.get("translation") if parsed else None,
            "usage": usage,
        }

    def transcribe_audio_bytes(
        self,
        audio_bytes: bytes,
        *,
        model_name: str = "models/gemini-2.5-flash-lite",
        prompt: Optional[str] = None,
        mime_type: str = "audio/wav",
        structured: bool = True,
        upload_when_large: bool = True,
        upload_threshold_bytes: int = INLINE_AUDIO_LIMIT_BYTES,
        wait_for_active_sec: int = 60,
    ) -> Dict[str, Any]:
        return self.transcribe_audio(
            audio_bytes,
            model_name=model_name,
            prompt=prompt,
            mime_type=mime_type,
            structured=structured,
            upload_when_large=upload_when_large,
            upload_threshold_bytes=upload_threshold_bytes,
            wait_for_active_sec=wait_for_active_sec
        )

    def _prepare_audio_part(
        self,
        audio_source: Union[str, Path, bytes],
        *,
        mime_type: Optional[str],
        upload_when_large: bool,
        upload_threshold_bytes: int,
    ) -> Tuple[Any, str]:
        if isinstance(audio_source, bytes):
            return {"mime_type": mime_type or "audio/wav", "data": audio_source}, "inline-bytes"

        path = Path(audio_source)
        if not path.exists():
            raise FileNotFoundError(f"Audio file not found: {path}")

        audio_bytes = path.read_bytes()
        guessed_mime = mime_type or mimetypes.guess_type(path.name)[0] or "audio/wav"

        if upload_when_large and len(audio_bytes) > upload_threshold_bytes:
            uploaded_file = self.client.upload_file(path, mime_type=guessed_mime)
            return {"mime_type": guessed_mime, "file_uri": uploaded_file.uri}, str(path)

        return {"mime_type": guessed_mime, "data": audio_bytes}, str(path)

    def _maybe_parse_structured_json(self, text: str, requested: bool) -> Dict[str, Any]:
        if not requested or not text:
            return {}
        stripped = self._strip_code_fences(text)
        try:
            payload = json.loads(stripped)
            return self._normalize_transcription_payload(payload)
        except (json.JSONDecodeError, TypeError):
            return {}

    @staticmethod
    def _log_usage_dict(usage: Dict[str, int], context: str = "") -> None:
        if not usage:
            return
        parts = [f"{k}={v}" for k, v in usage.items() if v]
        label = f"[{context}] " if context else ""
        print(f"LLM usage {label}{', '.join(parts)}")

    @staticmethod
    def _strip_code_fences(text: str) -> str:
        trimmed = text.strip()
        if trimmed.startswith("```"):
            parts = trimmed.splitlines()
            if parts: parts = parts[1:]
            if parts and parts[-1].strip().startswith("```"): parts = parts[:-1]
            trimmed = "\n".join(parts).strip()
        return trimmed

    @staticmethod
    def _normalize_transcription_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
        normalized = dict(payload)
        emotion = normalized.get("emotion")
        if isinstance(emotion, str): normalized["emotion"] = emotion.lower()
        return normalized

    @staticmethod
    def _normalize_model_name(model_name: str) -> str:
        if model_name.startswith("models/"): return model_name
        return f"models/{model_name}"

    @staticmethod
    def calculate_cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
        if not vec1 or not vec2: return 0.0
        v1, v2 = np.array(vec1), np.array(vec2)
        return np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))
