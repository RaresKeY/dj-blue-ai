import os
import platform

SERVICE_ID = "dj-blue-ai"
PRIMARY_KEY = "AI_STUDIO_API_KEY"
COMPAT_KEY = "AI_STUDIO"
KEY_NAMES = (PRIMARY_KEY, COMPAT_KEY)


def backend_display_name() -> str:
    system = platform.system()
    if system == "Linux":
        return "Secret Service (Seahorse)"
    if system == "Darwin":
        return "Keychain Access"
    if system == "Windows":
        return "Credential Manager"
    return "System Keychain"


def _import_keyring():
    try:
        import keyring  # type: ignore
        return keyring, None
    except Exception as exc:
        return None, str(exc)


def read_api_key():
    env_key = os.getenv(PRIMARY_KEY, "").strip()
    if env_key:
        if not os.getenv(COMPAT_KEY):
            os.environ[COMPAT_KEY] = env_key
        return env_key, None

    keyring, import_error = _import_keyring()
    if keyring is None:
        return None, f"Keyring backend unavailable: {import_error}"

    for key_name in KEY_NAMES:
        try:
            secret = keyring.get_password(SERVICE_ID, key_name)
        except Exception as exc:
            return None, f"Could not read keyring: {exc}"
        if secret:
            os.environ[PRIMARY_KEY] = secret
            os.environ[COMPAT_KEY] = secret
            return secret, None

    return None, None


def save_api_key(secret: str):
    cleaned = str(secret or "").strip()
    if not cleaned:
        return False, "API key cannot be empty."

    keyring, import_error = _import_keyring()
    if keyring is None:
        return False, f"Keyring backend unavailable: {import_error}"

    try:
        for key_name in KEY_NAMES:
            keyring.set_password(SERVICE_ID, key_name, cleaned)
    except Exception as exc:
        return False, f"Could not save key to keyring: {exc}"

    os.environ[PRIMARY_KEY] = cleaned
    os.environ[COMPAT_KEY] = cleaned
    return True, f"Saved API key to {backend_display_name()}."


def clear_api_key():
    keyring, import_error = _import_keyring()
    if keyring is None:
        os.environ.pop(PRIMARY_KEY, None)
        os.environ.pop(COMPAT_KEY, None)
        return False, f"Keyring backend unavailable: {import_error}"

    try:
        for key_name in KEY_NAMES:
            existing = keyring.get_password(SERVICE_ID, key_name)
            if existing:
                keyring.delete_password(SERVICE_ID, key_name)
    except Exception as exc:
        return False, f"Could not clear key from keyring: {exc}"

    os.environ.pop(PRIMARY_KEY, None)
    os.environ.pop(COMPAT_KEY, None)
    return True, f"Cleared API key from {backend_display_name()}."
