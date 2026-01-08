import json
import mimetypes
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import google.generativeai as genai
import numpy as np

MEET_TYPE_MOODS = "positive|neutral|tense|unfocused|collaborative|creative|unproductive"

CUSTOM_TRANSCRIPTION_PROMPT_MEET_TYPE = f"""
Process the audio file and generate a detailed transcription.

Requirements:
1. Detect the primary language.
2. If the recording is in a language different than English, also provide the English translation.
3. Identify the primary emotion of the speaker in this recording. You MUST choose exactly one of the following: {MEET_TYPE_MOODS}.
4. Provide a brief summary of the entire audio at the beginning.
5. Do no hallucinate speech if the audio is silent.

Respond ONLY as JSON matching:
{{
  "summary": "string",
  "content": "string",
  "translation": "string|None",
  "language_code": "string",
  "emotion": "{MEET_TYPE_MOODS}"
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
        """
        Initializes the singleton instance. The API key configuration only runs once.

        Args:
            api_key (str, optional): Your API key from Google AI Studio. 
                                     Required on first instantiation.
        """
        # The __init__ is called every time LLMUtilitySuite() is invoked,
        # but we use a flag to ensure the configuration runs only once.
        if not hasattr(self, 'is_initialized'):
            if api_key is None:
                raise ValueError("API key is required for the first initialization.")

            try:
                genai.configure(api_key=api_key)
                print("LLM API Suite configured successfully.")
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
        """
        Generates text content based on a user prompt and an optional system prompt.

        Args:
            prompt (str): The text prompt to send to the model.
            model_name (str, optional): The name of the model to use.
            system_prompt (str, optional): A system instruction to guide the model.

        Returns:
            str: The generated text response from the model.
        """
        try:
            model = genai.GenerativeModel(
                model_name,
                system_instruction=system_prompt
            )
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"An error occurred during text generation: {e}"

    def start_chat(
        self,
        model_name: str = "gemini-1.5-flash"
    ) -> genai.GenerativeModel.start_chat:
        """
        Initializes and starts a multi-turn chat session.

        Args:
            model_name (str, optional): The name of the model to use.

        Returns:
            A chat session object.
        """
        try:
            model = genai.GenerativeModel(model_name)
            chat = model.start_chat(history=[])
            return chat
        except Exception as e:
            print(f"Could not start chat session: {e}")
            return None

    @staticmethod
    def send_chat_message(
        chat_session,
        message: str
    ) -> str:
        """
        Sends a message in an ongoing chat session and gets the response.

        Args:
            chat_session: The chat session object from start_chat.
            message (str): The user's message to send.

        Returns:
            str: The model's response.
        """
        if not chat_session:
            return "Chat session is not initialized."
        try:
            response = chat_session.send_message(message)
            return response.text
        except Exception as e:
            return f"An error occurred during the chat: {e}"

    # --- EMBEDDING METHODS ---

    def get_embedding(
        self,
        text: str,
        model_name: str = "models/embedding-001",
        task_type: str = "RETRIEVAL_DOCUMENT"
    ) -> List[float]:
        """
        Generates an embedding for a single piece of text.

        Args:
            text (str): The text to embed.
            model_name (str, optional): The embedding model to use.
            task_type (str, optional): The intended task for the embedding.

        Returns:
            A list of floats representing the embedding vector.
        """
        try:
            result = genai.embed_content(
                model=model_name,
                content=text,
                task_type=task_type
            )
            return result['embedding']
        except Exception as e:
            print(f"An error occurred during embedding: {e}")
            return []

    def get_batch_embeddings(
        self,
        texts: List[str],
        model_name: str = "models/embedding-001",
        task_type: str = "RETRIEVAL_DOCUMENT"
    ) -> List[List[float]]:
        """
        Generates embeddings for a batch of texts.

        Args:
            texts (List[str]): A list of texts to embed.
            model_name (str, optional): The embedding model to use.
            task_type (str, optional): The intended task for the embeddings.

        Returns:
            A list of embedding vectors.
        """
        try:
            result = genai.embed_content(
                model=model_name,
                content=texts,
                task_type=task_type
            )
            return result['embedding']
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
        """
        Transcribes audio using the Gemini API and returns structured details when possible.

        Args:
            audio_source: Path to an audio file or raw audio bytes.
            model_name: Gemini model to use for transcription.
            prompt: Optional custom prompt; defaults to a detailed transcription prompt.
            mime_type: MIME type for raw bytes; guessed from file name when using paths.
            structured: When True, request JSON with summary/segments; falls back to text on failure.
            upload_when_large: Uploads files that exceed the inline size cap.
            upload_threshold_bytes: Inline audio byte ceiling before forcing upload.
            wait_for_active_sec: Seconds to wait for an uploaded file to become ACTIVE.

        Returns:
            A dict containing transcript text, optional summary and segments, and the raw response.
        """
        prompt = prompt or CUSTOM_TRANSCRIPTION_PROMPT_MEET_TYPE
        audio_part, source = self._prepare_audio_part(
            audio_source,
            mime_type=mime_type,
            upload_when_large=upload_when_large,
            upload_threshold_bytes=upload_threshold_bytes,
            wait_for_active_sec=wait_for_active_sec,
        )

        generation_config = None
        schema = self._transcription_schema_for_prompt(prompt) if structured else None
        if schema is not None:
            generation_config = self._build_generation_config(schema)

        try:
            normalized_model = self._normalize_model_name(model_name)
            model = genai.GenerativeModel(normalized_model)
            response = model.generate_content(
                contents=[prompt, audio_part],
                generation_config=generation_config,
            )
            self._log_usage(response, context="transcribe_audio")
        except Exception as e:
            return {
                "error": f"An error occurred during transcription: {e}",
                "source": source,
                "model": model_name,
            }

        parsed = self._maybe_parse_structured_response(response, structured)
        transcript_text = None
        if parsed:
            transcript_text = parsed.get("content")
        primary_emotion = parsed.get("emotion") if parsed else None

        return {
            "text": transcript_text.strip(),
            "summary": parsed.get("summary") if parsed else None,
            "emotion": primary_emotion,
            "raw_response": response,
            "source": source,
            "model": model_name,
            "translation": parsed.get("translation") if parsed else None,
        }

    def transcribe_audio_bytes(
        self,
        audio_bytes: bytes,
        *,
        model_name: str = "models/gemini-2.5-flash-lite",
        prompt: Optional[str] = None,
        mime_type: str = "audio/mp3",
        structured: bool = True,
        upload_when_large: bool = True,
        upload_threshold_bytes: int = INLINE_AUDIO_LIMIT_BYTES,
        wait_for_active_sec: int = 60,
    ) -> Dict[str, Any]:
        """
        Mirror `transcribe_audio` but operate directly on raw audio bytes.
        Keeps identical prompt defaults, schema/response handling, and return shape.
        """
        if not isinstance(audio_bytes, (bytes, bytearray)):
            return {"error": "audio_bytes must be bytes or bytearray."}
        if not mime_type:
            return {"error": "mime_type is required for raw audio bytes."}

        prompt = prompt or CUSTOM_TRANSCRIPTION_PROMPT_MEET_TYPE
        audio_part, source = self._prepare_audio_part(
            bytes(audio_bytes),
            mime_type=mime_type,
            upload_when_large=upload_when_large,
            upload_threshold_bytes=upload_threshold_bytes,
            wait_for_active_sec=wait_for_active_sec,
        )

        generation_config = None
        schema = self._transcription_schema_for_prompt(prompt) if structured else None
        if schema is not None:
            generation_config = self._build_generation_config(schema)

        try:
            normalized_model = self._normalize_model_name(model_name)
            model = genai.GenerativeModel(normalized_model)
            response = model.generate_content(
                contents=[prompt, audio_part],
                generation_config=generation_config,
            )
            self._log_usage(response, context="transcribe_audio_bytes")
        except Exception as e:
            return {
                "error": f"An error occurred during transcription: {e}",
                "source": source,
                "model": model_name,
            }

        parsed = self._maybe_parse_structured_response(response, structured)
        transcript_text = None
        if parsed:
            transcript_text = parsed.get("content")
        primary_emotion = parsed.get("emotion") if parsed else None

        return {
            "text": (transcript_text or "").strip(),
            "summary": parsed.get("summary") if parsed else None,
            "emotion": primary_emotion,
            "raw_response": response,
            "source": source,
            "model": model_name,
            "translation": parsed.get("translation") if parsed else None,
        }

    @staticmethod
    def _segments_to_text(segments: List[Dict[str, Any]]) -> str:
        return " ".join(seg.get("content", "").strip() for seg in segments if seg.get("content")).strip()

    @staticmethod
    def _extract_text(response: Any) -> str:
        """
        Robustly extract text from a Gemini response, even when .text is None.
        """
        text = getattr(response, "text", None)
        if text:
            return text

        candidates = getattr(response, "candidates", None) or []
        parts: List[str] = []
        for cand in candidates:
            content = getattr(cand, "content", None)
            if not content:
                continue
            for part in getattr(content, "parts", []) or []:
                part_text = getattr(part, "text", None)
                if part_text:
                    parts.append(part_text)
                    continue
                part_json = getattr(part, "json", None)
                if part_json is not None:
                    try:
                        parts.append(json.dumps(part_json))
                    except Exception:
                        continue
        return " ".join(parts).strip()

    @staticmethod
    def _log_usage(response: Any, *, context: str = "") -> None:
        usage = getattr(response, "usage_metadata", None) or getattr(response, "usageMetadata", None)
        if usage is None:
            return

        def _get(field: str):
            if isinstance(usage, dict):
                return usage.get(field)
            return getattr(usage, field, None)

        input_tokens = _get("input_token_count")
        output_tokens = _get("output_token_count")
        total_tokens = _get("total_token_count")

        if any(val is not None for val in (input_tokens, output_tokens, total_tokens)):
            parts: List[str] = []
            if input_tokens is not None:
                parts.append(f"input={input_tokens}")
            if output_tokens is not None:
                parts.append(f"output={output_tokens}")
            if total_tokens is not None:
                parts.append(f"total={total_tokens}")
            label = f"[{context}] " if context else ""
            print(f"LLM usage {label}{', '.join(parts)}")

    @staticmethod
    def _build_generation_config(response_schema) -> Optional[Any]:
        candidates = [
            getattr(genai, "GenerationConfig", None),
            getattr(getattr(genai, "types", None), "GenerationConfig", None),
        ]
        for candidate in candidates:
            if candidate is None:
                continue
            try:
                return candidate(
                    response_mime_type="application/json",
                    response_schema=response_schema,
                )
            except Exception:
                continue
        return None

    @staticmethod
    def _transcription_schema_for_prompt(prompt: Optional[str]):
        """
        Pick a response schema that matches the prompt shape.
        """
        try:
            schema_cls = genai.types.Schema
            type_enum = genai.types.Type
        except Exception:
            return None

        if prompt and prompt.strip() == CUSTOM_TRANSCRIPTION_PROMPT_MEET_TYPE:
            return schema_cls(
                type=type_enum.OBJECT,
                properties={
                    "summary": schema_cls(type=type_enum.STRING, description="Brief summary of the audio."),
                    "content": schema_cls(type=type_enum.STRING, description="Full transcription text."),
                    "translation": schema_cls(type=type_enum.STRING, description="English translation when applicable."),
                    "language_code": schema_cls(type=type_enum.STRING, description="Primary language code."),
                    "emotion": schema_cls(
                        type=type_enum.STRING,
                        enum=["positive", "neutral", "tense", "unfocused", "collaborative", "creative", "unproductive"],
                    ),
                },
                required=["summary", "content", "language_code", "emotion"],
            )

        return schema_cls(
            type=type_enum.OBJECT,
            properties={
                "summary": schema_cls(
                    type=type_enum.STRING,
                    description="A concise summary of the audio content.",
                ),
                "segments": schema_cls(
                    type=type_enum.ARRAY,
                    description="List of transcribed segments with speaker and timestamp.",
                    items=schema_cls(
                        type=type_enum.OBJECT,
                        properties={
                            "speaker": schema_cls(type=type_enum.STRING),
                            "timestamp": schema_cls(type=type_enum.STRING),
                            "content": schema_cls(type=type_enum.STRING),
                            "language": schema_cls(type=type_enum.STRING),
                            "language_code": schema_cls(type=type_enum.STRING),
                            "translation": schema_cls(type=type_enum.STRING),
                            "emotion": schema_cls(
                                type=type_enum.STRING,
                                enum=["happy", "sad", "angry", "neutral"],
                            ),
                        },
                        required=["speaker", "timestamp", "content", "language", "language_code", "emotion"],
                    ),
                ),
            },
            required=["summary", "segments"],
        )

    @staticmethod
    def _maybe_parse_structured_response(response: Any, structured_requested: bool) -> Dict[str, Any]:
        if not structured_requested:
            return {}
        candidates: List[str] = []
        top_text = getattr(response, "text", None)
        if top_text:
            candidates.append(top_text)

        for cand in getattr(response, "candidates", []) or []:
            content = getattr(cand, "content", None)
            if not content:
                continue
            for part in getattr(content, "parts", []) or []:
                part_text = getattr(part, "text", None)
                if part_text:
                    candidates.append(part_text)
                    continue
                part_json = getattr(part, "json", None)
                if part_json is not None:
                    try:
                        candidates.append(json.dumps(part_json))
                    except Exception:
                        continue

        for raw in candidates:
            stripped = LLMUtilitySuite._strip_code_fences(raw)
            try:
                payload = json.loads(stripped)
                return LLMUtilitySuite._normalize_transcription_payload(payload)
            except (json.JSONDecodeError, TypeError):
                continue
        return {}

    @staticmethod
    def _strip_code_fences(text: str) -> str:
        """
        Remove leading/trailing markdown code fences to recover JSON.
        """
        trimmed = text.strip()
        if trimmed.startswith("```"):
            # Drop first fence line
            parts = trimmed.splitlines()
            # Remove first line and any trailing fence line
            if parts:
                parts = parts[1:]
            if parts and parts[-1].strip().startswith("```"):
                parts = parts[:-1]
            trimmed = "\n".join(parts).strip()
        return trimmed

    @staticmethod
    def _normalize_transcription_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize casing/fields in transcription payload.
        """
        normalized = dict(payload)
        top_emotion = normalized.get("emotion")
        if isinstance(top_emotion, str):
            normalized["emotion"] = top_emotion.lower()

        segments = payload.get("segments") or []
        normalized_segments = []
        for seg in segments:
            emotion = seg.get("emotion")
            if isinstance(emotion, str):
                seg = {**seg, "emotion": emotion.lower()}
            normalized_segments.append(seg)
        if segments:
            normalized["segments"] = normalized_segments

        return normalized

    @staticmethod
    def _normalize_model_name(model_name: str) -> str:
        """
        Ensure we pass fully-qualified model IDs (e.g., models/gemini-2.5-flash).
        """
        if model_name.startswith("models/"):
            return model_name
        return f"models/{model_name}"

    def _prepare_audio_part(
        self,
        audio_source: Union[str, Path, bytes],
        *,
        mime_type: Optional[str],
        upload_when_large: bool,
        upload_threshold_bytes: int,
        wait_for_active_sec: int,
    ) -> Tuple[Any, str]:
        if isinstance(audio_source, bytes):
            # Default to 16-bit little-endian PCM if no MIME provided.
            fallback_mime = "audio/raw; encoding=signed-integer; bits=16; rate=44100; channels=2"
            return {"mime_type": mime_type or fallback_mime, "data": audio_source}, "inline-bytes"

        path = Path(audio_source)
        if not path.exists():
            raise FileNotFoundError(f"Audio file not found: {path}")

        audio_bytes = path.read_bytes()
        guessed_mime = mime_type or mimetypes.guess_type(path.name)[0] or "audio/wav"

        if upload_when_large and len(audio_bytes) > upload_threshold_bytes:
            uploaded = genai.upload_file(path=str(path))
            ready = self._wait_for_file_active(uploaded, wait_for_active_sec)
            return ready, str(path)

        return LLMUtilitySuite._make_audio_part(guessed_mime, audio_bytes), str(path)

    @staticmethod
    def _make_audio_part(mime_type: str, audio_bytes: bytes) -> Any:
        try:
            part_cls = getattr(getattr(genai, "types", None), "Part", None)
            if part_cls:
                return part_cls.from_bytes(data=audio_bytes, mime_type=mime_type)
        except Exception:
            pass
        return {"mime_type": mime_type, "data": audio_bytes}

    @staticmethod
    def _wait_for_file_active(uploaded_file: Any, timeout_sec: int) -> Any:
        deadline = time.time() + timeout_sec
        current = uploaded_file
        while time.time() < deadline:
            state = getattr(current, "state", None)
            if state is None or state == "ACTIVE":
                return current
            time.sleep(2)
            try:
                current = genai.get_file(current.name)
            except Exception:
                break
        return current

    # --- UTILITY METHOD ---

    @staticmethod
    def list_available_models(supports_generate: bool = False) -> List[str]:
        """
        Returns available model names, optionally filtered for text generation support.

        Args:
            supports_generate (bool, optional): When True, only include models that
                                                support `generateContent`.

        Returns:
            List[str]: Model identifiers exposed by the API.
        """
        try:
            models = genai.list_models()
            if supports_generate:
                return [
                    model.name
                    for model in models
                    if "generateContent" in getattr(model, "supported_generation_methods", [])
                ]
            return [model.name for model in models]
        except Exception as e:
            print(f"Unable to list models: {e}")
            return []

    @staticmethod
    def calculate_cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
        """
        Calculates the cosine similarity between two embedding vectors.

        Args:
            vec1 (List[float]): The first embedding vector.
            vec2 (List[float]): The second embedding vector.

        Returns:
            The cosine similarity score (from -1 to 1).
        """
        if not vec1 or not vec2:
            return 0.0
        vec1 = np.array(vec1)
        vec2 = np.array(vec2)
        return np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))
