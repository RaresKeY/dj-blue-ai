import datetime
import typing

from ui_ux_team.blue_ui import settings as app_settings
from architects.helpers.genai_client import GenAIClient, GenAIChatSession
from ui_ux_team.blue_ui.app.api_usage_guard import record_usage, reserve_request

# Default System Instruction from blue_bird_chat.py
DEFAULT_SYSTEM_INSTRUCTION = (
    "You are a helpful analyst assistant whose knowledge is primarily grounded in the provided TRANSCRIPT. "
    "Adhere to the following guidelines when answering:\n"
    "1. **Priority**: Always attempt to answer using the transcript first.\n"
    "2. **Out of Scope**: If the user asks about a topic not found in the transcript, you must explicitly state that the topic is 'outside the scope of the lesson.'\n"
    "3. **General Knowledge**: After the disclaimer, provide accurate, factual information about the topic using your general knowledge.\n"
    "4. **Synthesis**: If applicable, draw parallels or comparisons between this outside information and concepts found in the transcript.\n"
    "Constraint: Maintain strict factual accuracy and do not hallucinate information."
)

class GeminiChatbot:
    """
    A generic, plug-and-play chatbot component wrapping the GenAIClient compatibility layer.
    """
    def __init__(
        self,
        api_key: str,
        model_name: str = None,
        system_instruction: str = DEFAULT_SYSTEM_INSTRUCTION,
    ):
        self.api_key = api_key
        self.model_name = self._normalize_model_name(model_name or app_settings.chatbot_model())
        self.system_instruction = system_instruction
        self.client = GenAIClient(api_key=api_key)
        self.chat_session = None
        self.current_transcript = ""
        self.last_error = ""
        self.cached_content_name = None

    @staticmethod
    def _normalize_model_name(model_name: str) -> str:
        if model_name.startswith("models/"):
            return model_name
        return f"models/{model_name}"

    def update_context_with_file(self, file_path: str) -> bool:
        try:
            self.last_error = ""
            with open(file_path, 'r', encoding='utf-8') as f:
                new_content = f.read()
            self.current_transcript = new_content
            return self.load_context(self.current_transcript)
        except Exception as e:
            self.last_error = f"Error updating context from file: {e}"
            return False

    def load_context(self, transcript_text: str, ttl_minutes: int = 10) -> bool:
        """
        Sets up the context for the chat session. Uses context caching for long transcripts.
        """
        self.last_error = ""
        self.current_transcript = transcript_text or ""
        transcript_for_cache = self.current_transcript.strip()
        
        config = {"system_instruction": self.system_instruction}
        
        # New SDK Context Caching Logic (Simplified for the compatibility layer)
        # Note: If context caching is needed, we'd add it to GenAIClient.
        # For now, we follow the "preserve behavior" rule by using history for context.
        
        try:
            history = []
            if transcript_for_cache:
                history = [
                    {"role": "user", "parts": [{"text": f"Use the following transcript as context:\n\n{transcript_for_cache}"}]},
                    {"role": "model", "parts": [{"text": "Understood. I will prioritize the transcript context."}]}
                ]
            
            self.chat_session = GenAIChatSession(
                client=self.client.client,
                model_name=self.model_name,
                history=history,
                config=config
            )
            return True
        except Exception as e:
            self.last_error = f"Error loading context: {e}"
            return False

    def send_message(self, message: str) -> typing.Dict:
        if not self.chat_session:
             return {"error": "Chat session not initialized. Please load context first."}

        try:
            allowed, reason = reserve_request("chat", model_name=self.model_name)
            if not allowed:
                return {"error": reason, "limit_blocked": True}

            response = self.chat_session.send_message(message)
            usage = response.get("usage", {})
            record_usage(scope="chat", model_name=self.model_name, usage=usage)

            return {
                "text": response.get("text", ""),
                "usage": usage
            }
        except Exception as e:
            return {"error": str(e)}

    def get_token_count(self) -> int:
        # In the new SDK, we'd need to call client.models.count_tokens
        return 0
