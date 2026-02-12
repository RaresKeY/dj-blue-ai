import sys
import os
from pathlib import Path

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        # Check if running from the specific py_learn.py location or project root
        # This logic attempts to find the project root if not frozen
        base_path = os.path.abspath(".")
        
        # specific fix for the current project structure if running from project root
        if not os.path.exists(os.path.join(base_path, relative_path)):
             # try relative to the script location if provided?
             # But for this project, we want relative to Project Root usually
             pass
             
    return os.path.join(base_path, relative_path)

def get_project_root():
    """Returns the project root directory."""
    try:
        if getattr(sys, 'frozen', False):
            # If frozen, the executable is inside the dist folder or tmp
            # We likely want the folder *containing* the executable
            return os.path.dirname(sys.executable)
        else:
             return Path(__file__).resolve().parents[2]
    except Exception:
        return os.getcwd()
