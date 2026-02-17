import os
from dotenv import load_dotenv

from ui_ux_team.blue_ui.app.secure_api_key import COMPAT_KEY, PRIMARY_KEY, read_api_key

def init_env():
    """
    Hybrid Loader:
    1. Tries to fetch secrets from System Keyring (Seahorse)
    2. Falls back to .env file if Keyring is empty
    """
    print("--- Loading Configuration ---")

    # 1. Try to inject from OS Keychain (Seahorse / Keychain / Credential Manager).
    secret, _ = read_api_key()
    if secret:
        print(f"✅ Loaded {PRIMARY_KEY} from System Keychain")

    # 2. Run load_dotenv (Teammate's Workflow)
    # By default, override=False. It will NOT overwrite what we just set from Keyring.
    # It will only fill in gaps from the .env file.
    load_dotenv()
    env_key = os.getenv(PRIMARY_KEY, "").strip()
    if env_key and not os.getenv(COMPAT_KEY):
        os.environ[COMPAT_KEY] = env_key

# Run the initialization immediately when this module is imported
init_env()
