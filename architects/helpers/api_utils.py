import google.generativeai as genai
import numpy as np
from typing import List, Union, Dict

class LLMUtilitySuite:
    """
    A singleton class to manage interactions with a Large Language Model API.
    This suite handles API configuration, text generation (with system prompts),
    chat sessions, and text embeddings.
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
