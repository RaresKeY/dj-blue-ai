"""
Compatibility layer for Google GenAI SDK.
Handles transition from google.generativeai to google.genai.
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from google import genai
from google.genai import types


class GenAIClient:
    """
    Unified client for Gemini API using the supported google.genai SDK.
    Provides normalization for response metadata and file polling.
    """

    def __init__(self, api_key: str):
        self.client = genai.Client(api_key=api_key)

    def generate_content(
        self,
        model_name: str,
        contents: Union[str, List[Any]],
        config: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Generic content generation wrapper with metadata normalization."""
        normalized_contents = self._normalize_contents(contents)
        response = self.client.models.generate_content(
            model=model_name, contents=normalized_contents, config=config
        )
        return self._normalize_response(response)

    def _normalize_contents(self, contents: Union[str, List[Any]]) -> List[Any]:
        """Converts legacy dictionaries into SDK-compatible Part objects."""
        if isinstance(contents, str):
            return [contents]
        
        normalized = []
        for item in contents:
            if isinstance(item, dict):
                # Handle legacy audio data/mime_type dicts
                if "data" in item and "mime_type" in item:
                    normalized.append(types.Part.from_bytes(data=item["data"], mime_type=item["mime_type"]))
                elif "file_uri" in item and "mime_type" in item:
                    normalized.append(types.Part.from_uri(file_uri=item["file_uri"], mime_type=item["mime_type"]))
                else:
                    normalized.append(item)
            else:
                normalized.append(item)
        return normalized

    def embed_content(
        self, model_name: str, contents: Union[str, List[str]]
    ) -> List[List[float]]:
        """Embed content wrapper."""
        response = self.client.models.embed_content(model=model_name, contents=contents)
        if hasattr(response, "embeddings"):
            return [e.values for e in response.embeddings]
        return []

    def upload_file(self, file_path: Union[str, Path], mime_type: Optional[str] = None) -> Any:
        """Upload file and wait for processing if needed."""
        path = Path(file_path)
        uploaded = self.client.files.upload(path=str(path), config={"mime_type": mime_type})

        # Active polling for file processing state (needed for large audio/video)
        while uploaded.state.name == "PROCESSING":
            time.sleep(2)
            uploaded = self.client.files.get(name=uploaded.name)

        if uploaded.state.name == "FAILED":
            raise RuntimeError(f"File processing failed: {uploaded.name}")

        return uploaded

    def _normalize_response(self, response: Any) -> Dict[str, Any]:
        """Normalizes SDK response into a consistent dictionary format."""
        normalized = {
            "text": response.text,
            "usage": {},
            "raw_response": response,
        }

        # Extract usage metadata if available
        if hasattr(response, "usage_metadata") and response.usage_metadata:
            u = response.usage_metadata
            normalized["usage"] = {
                "prompt_tokens": getattr(u, "prompt_token_count", 0),
                "candidates_tokens": getattr(u, "candidates_token_count", 0),
                "total_tokens": getattr(u, "total_token_count", 0),
                "cached_tokens": getattr(u, "cached_content_token_count", 0),
            }

        return normalized


class GenAIChatSession:
    """Wrapper for chat sessions to maintain history and normalization."""

    def __init__(self, client: genai.Client, model_name: str, history: Optional[List[Dict]] = None, config: Optional[Dict] = None):
        self.client = client
        self.model_name = model_name
        self.history = history or []
        self.config = config

    def send_message(self, message: str) -> Dict[str, Any]:
        """Sends a message and updates local history shim."""
        # Note: google.genai has its own chat session, but we shim it here for stable control.
        # Alternatively, we could use client.chats.create()
        self.history.append({"role": "user", "parts": [{"text": message}]})
        
        # Normalize history before sending
        normalized_history = self._normalize_history(self.history)
        
        response = self.client.models.generate_content(
            model=self.model_name,
            contents=normalized_history,
            config=self.config
        )
        
        normalized = self._normalize_response(response)
        if normalized.get("text"):
            self.history.append({"role": "model", "parts": [{"text": normalized["text"]}]})
            
        return normalized

    def _normalize_history(self, history: List[Dict]) -> List[Any]:
        """Ensures history entries match the new SDK's expectation."""
        normalized = []
        for turn in history:
            role = turn.get("role")
            parts = turn.get("parts", [])
            norm_parts = []
            for p in parts:
                if isinstance(p, dict):
                    if "text" in p:
                        norm_parts.append(types.Part.from_text(text=p["text"]))
                    elif "data" in p and "mime_type" in p:
                        norm_parts.append(types.Part.from_bytes(data=p["data"], mime_type=p["mime_type"]))
                    elif "file_uri" in p and "mime_type" in p:
                        norm_parts.append(types.Part.from_uri(file_uri=p["file_uri"], mime_type=p["mime_type"]))
                    else:
                        norm_parts.append(p)
                else:
                    norm_parts.append(p)
            normalized.append(types.Content(role=role, parts=norm_parts))
        return normalized

    def _normalize_response(self, response: Any) -> Dict[str, Any]:
        # Implementation duplicated or shared with GenAIClient
        normalized = {
            "text": response.text,
            "usage": {},
        }
        if hasattr(response, "usage_metadata") and response.usage_metadata:
            u = response.usage_metadata
            normalized["usage"] = {
                "prompt_tokens": getattr(u, "prompt_token_count", 0),
                "candidates_tokens": getattr(u, "candidates_token_count", 0),
                "total_tokens": getattr(u, "total_token_count", 0),
                "cached_tokens": getattr(u, "cached_content_token_count", 0),
            }
        return normalized
