import os
import keyring
from dotenv import load_dotenv

# --- CONFIGURATION ---
SERVICE_ID = "dj-blue-ai"
KEYS_TO_FETCH = ["AI_STUDIO", "AI_STUDIO_API_KEY"]

def init_env():
    """
    Hybrid Loader:
    1. Tries to fetch secrets from System Keyring (Seahorse)
    2. Falls back to .env file if Keyring is empty
    """
    print("--- Loading Configuration ---")

    # 1. Try to inject from Keyring (Your Secure Workflow)
    for key_name in KEYS_TO_FETCH:
        try:
            # Attempt to fetch from Seahorse
            secret = keyring.get_password(SERVICE_ID, key_name)

            if secret:
                # Inject into RAM (Environment Variable)
                os.environ[key_name] = secret
                print(f"✅ Loaded {key_name} from System Keyring")
        except Exception as e:
            # If keyring fails/isn't set up, just ignore it
            pass

    # 2. Run load_dotenv (Teammate's Workflow)
    # By default, override=False. It will NOT overwrite what we just set from Keyring.
    # It will only fill in gaps from the .env file.
    load_dotenv()

# Run the initialization immediately when this module is imported
init_env()