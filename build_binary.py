import PyInstaller.__main__
import os
import shutil
from pathlib import Path

def build():
    # Define paths
    base_dir = Path(__file__).parent
    entry_point = base_dir / "ui_ux_team" / "prototype_r" / "py_learn.py"
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
    
    # ui_ux_team/prototype_r/assets -> ui_ux_team/prototype_r/assets
    assets_source = base_dir / "ui_ux_team" / "prototype_r" / "assets"
    assets_dest = "ui_ux_team/prototype_r/assets"
    
    # mood_readers/data -> mood_readers/data
    mood_data_source = base_dir / "mood_readers" / "data"
    mood_data_dest = "mood_readers/data"

    datas = [
        f"--add-data={assets_source}{os.pathsep}{assets_dest}",
        f"--add-data={mood_data_source}{os.pathsep}{mood_data_dest}",
    ]

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
    ] + hidden_imports + datas

    print("Starting PyInstaller build...")
    PyInstaller.__main__.run(args)
    print("Build complete.")

    # Post-build actions: 
    # Copy .env if it exists (for API key)
    env_file = base_dir / ".env"
    if env_file.exists():
        shutil.copy(env_file, dist_dir / ".env")
        print(f"Copied .env to {dist_dir / '.env'}")
    else:
        print("Warning: .env file not found. Please create one next to the executable.")

if __name__ == "__main__":
    build()
