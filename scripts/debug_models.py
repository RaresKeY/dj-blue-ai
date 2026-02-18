
import sys
from pathlib import Path

# Ensure project root is importable
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from architects.helpers.genai_client import GenAIClient
from ui_ux_team.blue_ui.app.secure_api_key import read_api_key

def main():
    api_key, _ = read_api_key()
    if not api_key:
        print("No API key found.")
        return
    
    client = GenAIClient(api_key=api_key)
    models = client.list_models()
    
    if not models:
        print("No models returned.")
        return
        
    m = models[0]
    print(f"Model object type: {type(m)}")
    print(f"Attributes: {dir(m)}")
    
    for m in models:
        # Check supported methods
        methods = getattr(m, 'supported_generation_methods', [])
        print(f"Model: {m.name} | Methods: {methods}")
        if 'generateContent' in str(methods):
            print(f"  -> Valid for text generation")

if __name__ == "__main__":
    main()
