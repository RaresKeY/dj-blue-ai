import google.generativeai as genai
from google.generativeai import caching
import datetime
import typing

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
    A generic, plug-and-play chatbot component wrapping Google's GenAI SDK
    with Context Caching support.
    """
    def __init__(
        self,
        api_key: str,
        model_name: str = "models/gemini-2.5-flash-lite",
        system_instruction: str = DEFAULT_SYSTEM_INSTRUCTION,
    ):
        """
        Initialize the Gemini Chatbot.

        Args:
            api_key (str): Google AI Studio API Key.
            model_name (str): The model version to use (e.g., "gemini-3-pro-preview").
            system_instruction (str): System prompt to guide the model's behavior.
        """
        self.api_key = api_key
        self.model_name = self._normalize_model_name(model_name)
        self.system_instruction = system_instruction
        self.cache = None
        self.model = None
        self.chat_session = None
        self.current_transcript = ""
        self.last_error = ""
        
        # Configure the API globally for this process
        if self.api_key:
            genai.configure(api_key=self.api_key)

    @staticmethod
    def _normalize_model_name(model_name: str) -> str:
        if model_name.startswith("models/"):
            return model_name
        return f"models/{model_name}"

    @staticmethod
    def _build_transcript_history(transcript_text: str) -> typing.List[dict]:
        cleaned = (transcript_text or "").strip()
        if not cleaned:
            return []

        return [
            {
                "role": "user",
                "parts": [
                    "Use the following transcript as the primary context for this session.\n\n"
                    f"TRANSCRIPT:\n{cleaned}"
                ],
            },
            {
                "role": "model",
                "parts": ["Understood. I will prioritize the transcript context in my responses."],
            },
        ]

    def update_context_with_file(self, file_path: str) -> bool:
        """
        Reads a text file, replaces the current context with its content,
        and reloads the cache.

        Args:
            file_path (str): Path to the .txt file.

        Returns:
            bool: True if successful, False otherwise.
        """
        try:
            self.last_error = ""
            with open(file_path, 'r', encoding='utf-8') as f:
                new_content = f.read()
            
            # Replace existing transcript with new file content
            self.current_transcript = new_content

            return self.load_context(self.current_transcript)
        except Exception as e:
            self.last_error = f"Error updating context from file: {e}"
            print(self.last_error)
            return False

    def load_context(self, transcript_text: str, ttl_minutes: int = 10) -> bool:
        """
        Creates a CachedContent object for the provided transcript.
        This sets up the 'knowledge base' for the chat session.

        Args:
            transcript_text (str): The content to cache.
            ttl_minutes (int): Time-to-live for the cache in minutes.

        Returns:
            bool: True if successful, False otherwise.
        """
        self.last_error = ""
        self.current_transcript = transcript_text or ""
        transcript_for_cache = self.current_transcript.strip()
        cache_error = None

        self.cache = None
        self.model = None
        self.chat_session = None

        # Try context caching first when transcript has meaningful content.
        if len(transcript_for_cache) >= 1000:
            try:
                print(f"--- Creating Context Cache (Model: {self.model_name}) ---")
                self.cache = caching.CachedContent.create(
                    model=self.model_name,
                    display_name='transcript_cache',
                    system_instruction=self.system_instruction,
                    contents=[self.current_transcript],
                    ttl=datetime.timedelta(minutes=ttl_minutes)
                )
                self.model = genai.GenerativeModel.from_cached_content(cached_content=self.cache)
                self.start_new_chat()
                return True
            except Exception as e:
                cache_error = e

        # Fallback to non-cached chat so BlueBird still works when cache creation fails.
        try:
            self.model = genai.GenerativeModel(
                model_name=self.model_name,
                system_instruction=self.system_instruction,
            )
            history = self._build_transcript_history(self.current_transcript)
            self.start_new_chat(history=history)
            if cache_error:
                print(f"Context cache unavailable, continuing without cache: {cache_error}")
            return True
        except Exception as e:
            if cache_error:
                self.last_error = f"Cache init failed ({cache_error}); fallback init failed ({e})"
            else:
                self.last_error = f"Error loading context: {e}"
            print(self.last_error)
            return False

    def start_new_chat(self, history: typing.List[dict] = None):
        """
        Starts or restarts the chat session.
        
        Args:
            history (list): Optional list of history in Google's format 
                            [{"role": "user", "parts": [...]}, ...] "
        """
        if self.model:
            self.chat_session = self.model.start_chat(history=history or [])
        else:
            raise RuntimeError("Model not initialized. Call load_context() first.")

    def send_message(self, message: str) -> typing.Dict:
        """
        Sends a message to the chat session and returns the response.

        Args:
            message (str): The user's message.

        Returns:
            dict: Contains 'text' (response string), 'usage' (token counts), 
                  or 'error' if something went wrong.
        """
        if not self.chat_session:
             return {"error": "Chat session not initialized. Please load a transcript first."}

        try:
            response = self.chat_session.send_message(message)
            
            # Extract usage metadata if available
            usage = {}
            if response.usage_metadata:
                u = response.usage_metadata
                usage = {
                    "prompt_tokens": u.prompt_token_count,
                    "candidates_tokens": u.candidates_token_count,
                    "total_tokens": u.total_token_count,
                    "cached_tokens": getattr(u, "cached_content_token_count", 0)
                }

            return {
                "text": response.text,
                "usage": usage
            }
        except Exception as e:
            return {"error": str(e)}

    def get_token_count(self) -> int:
        """Returns the total token count of the cached content (if active)."""
        if self.cache and self.cache.usage_metadata:
            return self.cache.usage_metadata.total_token_count
        return 0
