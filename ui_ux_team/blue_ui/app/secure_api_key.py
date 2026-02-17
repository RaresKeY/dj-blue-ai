import platform

SERVICE_ID = "dj-blue-ai"
PRIMARY_KEY = "AI_STUDIO_API_KEY"
COMPAT_KEY = "AI_STUDIO"
KEY_NAMES = (PRIMARY_KEY, COMPAT_KEY)
RUNTIME_SOURCE_KEYRING = "keyring"
RUNTIME_SOURCE_PROCESS_ENV = "process_env"
RUNTIME_SOURCE_DOTENV = "dotenv"

_RUNTIME_API_KEY = ""
_RUNTIME_API_SOURCE = ""


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


def runtime_api_key() -> str:
    return str(_RUNTIME_API_KEY or "").strip()


def runtime_api_key_source() -> str:
    return str(_RUNTIME_API_SOURCE or "").strip()


def set_runtime_api_key(secret: str, source: str = "") -> None:
    global _RUNTIME_API_KEY, _RUNTIME_API_SOURCE
    cleaned = str(secret or "").strip()
    if not cleaned:
        clear_runtime_api_key()
        return
    _RUNTIME_API_KEY = cleaned
    _RUNTIME_API_SOURCE = str(source or "").strip()


def clear_runtime_api_key() -> None:
    global _RUNTIME_API_KEY, _RUNTIME_API_SOURCE
    _RUNTIME_API_KEY = ""
    _RUNTIME_API_SOURCE = ""


def read_api_key():
    keyring, import_error = _import_keyring()
    if keyring is None:
        return None, f"Keyring backend unavailable: {import_error}"

    for key_name in KEY_NAMES:
        try:
            secret = keyring.get_password(SERVICE_ID, key_name)
        except Exception as exc:
            return None, f"Could not read keyring: {exc}"
        if secret:
            set_runtime_api_key(secret, source=RUNTIME_SOURCE_KEYRING)
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

    set_runtime_api_key(cleaned, source=RUNTIME_SOURCE_KEYRING)
    return True, f"Saved API key to {backend_display_name()}."


def clear_api_key():
    keyring, import_error = _import_keyring()
    if keyring is None:
        clear_runtime_api_key()
        return False, f"Keyring backend unavailable: {import_error}"

    try:
        for key_name in KEY_NAMES:
            existing = keyring.get_password(SERVICE_ID, key_name)
            if existing:
                keyring.delete_password(SERVICE_ID, key_name)
    except Exception as exc:
        return False, f"Could not clear key from keyring: {exc}"

    clear_runtime_api_key()
    return True, f"Cleared API key from {backend_display_name()}."
