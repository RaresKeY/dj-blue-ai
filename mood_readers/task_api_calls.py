import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from architects.helpers.api_utils import LLMUtilitySuite

# Exercise 1: With the help of a ChatBot, set up an AI Studio API key, replace "API_KEY" with your key
API_KEY = "API_KEY"
MODEL = "gemini-flash-latest"

# Example usage:
llm_suite = LLMUtilitySuite(API_KEY) # instantiate class
message = "Hello and welcome to the show" # transcript
system_message = "You are a mood AI. give me some moods based on provided transcript, plaintext" # instructions

response = llm_suite.generate_text(
            model_name=MODEL,
            prompt=message,
            system_prompt=system_message
            )

print(response)

# Exercise 2: Get a json response mapped to a list of moods

# Exercise 3: Experiment with different messages and data

# Exercise 4: Save response to file

# Exercise 5: (Optional) Using a ChatBot, create your own script that makes AI Studio API calls without the helper class
