import PyInstaller.__main__
import os
import shutil
from pathlib import Path
import sys

def build():
    # Define paths
    base_dir = Path(__file__).parent
    entry_point = base_dir / "ui_ux_team" / "blue_ui" / "app" / "main.py"
    dist_dir = base_dir / "dist"
    build_dir = base_dir / "build"
    
    # Clean previous builds
    if dist_dir.exists():
        shutil.rmtree(dist_dir)
    if build_dir.exists():
        shutil.rmtree(build_dir)

    # Hidden imports for complex libraries
    hidden_imports = [
        "--hidden-import=librosa",
        "--hidden-import=sklearn.utils._typedefs",
        "--hidden-import=sklearn.neighbors._partition_nodes",
        "--hidden-import=scipy.special.cython_special",
        "--hidden-import=audioread",
        "--hidden-import=resampy",
        "--hidden-import=soundfile",
        "--hidden-import=pyaudio",
        "--hidden-import=miniaudio",
        "--hidden-import=pkg_resources.py2_warn",
        "--hidden-import=google.generativeai",
        "--hidden-import=architects",
        "--hidden-import=mood_readers",
        "--hidden-import=ui_ux_team",
    ]

    # Data files (assets)
    # Format: source:dest
    # We need to preserve the structure expected by resource_path
    
    # ui_ux_team/assets -> ui_ux_team/assets
    assets_source = base_dir / "ui_ux_team" / "assets"
    assets_dest = "ui_ux_team/assets"
    
    # mood_readers/data -> mood_readers/data
    mood_data_source = base_dir / "mood_readers" / "data"
    mood_data_dest = "mood_readers/data"

    datas = [
        f"--add-data={assets_source}{os.pathsep}{assets_dest}",
        f"--add-data={mood_data_source}{os.pathsep}{mood_data_dest}",
    ]

    icon_args = []
    icon_root = base_dir / "ui_ux_team" / "assets" / "app_icons"
    if sys.platform.startswith("win"):
        candidate = icon_root / "windows" / "dj-blue-ai.ico"
    elif sys.platform == "darwin":
        candidate = icon_root / "macos" / "dj-blue-ai.icns"
    else:
        candidate = icon_root / "linux" / "512.png"
    if candidate.exists():
        icon_args.append(f"--icon={candidate}")
    else:
        print(f"Warning: platform icon not found, building without --icon: {candidate}")

    # PyInstaller arguments
    args = [
        str(entry_point),
        "--name=dj-blue-ai",
        "--onefile",  # Create a single executable
        "--windowed", # No console window (GUI app)
        "--clean",
        "--exclude-module=PyQt6",
        "--exclude-module=PyQt5",
        # "--log-level=WARN",
    ] + hidden_imports + datas + icon_args

    print("Starting PyInstaller build...")
    PyInstaller.__main__.run(args)
    print("Build complete.")

    # Do not copy .env into build outputs.
    # API keys should be sourced from OS keychain at runtime.
    print("Skipped .env copy for security. Use OS keychain or local runtime environment variables.")

if __name__ == "__main__":
    build()
