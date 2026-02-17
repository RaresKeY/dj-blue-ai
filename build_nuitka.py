import shutil
import subprocess
import sys
from pathlib import Path


def _platform_icon_arg(base_dir: Path) -> list[str]:
    icon_root = base_dir / "ui_ux_team" / "assets" / "app_icons"
    if sys.platform.startswith("win"):
        icon_path = icon_root / "windows" / "dj-blue-ai.ico"
        return [f"--windows-icon-from-ico={icon_path}"] if icon_path.exists() else []
    if sys.platform == "darwin":
        icon_path = icon_root / "macos" / "dj-blue-ai.icns"
        return [f"--macos-app-icon={icon_path}"] if icon_path.exists() else []
    return []


def build() -> None:
    base_dir = Path(__file__).resolve().parent
    entry_point = base_dir / "ui_ux_team" / "blue_ui" / "app" / "main.py"
    output_dir = base_dir / "dist_nuitka"
    cache_dir = base_dir / "build_nuitka"

    if output_dir.exists():
        shutil.rmtree(output_dir)
    if cache_dir.exists():
        shutil.rmtree(cache_dir)

    common_args = [
        sys.executable,
        "-m",
        "nuitka",
        "--standalone",
        "--assume-yes-for-downloads",
        "--enable-plugin=pyside6",
        "--output-dir=" + str(output_dir),
        "--output-filename=dj-blue-ai",
        "--remove-output",
        "--include-data-dir=ui_ux_team/assets=ui_ux_team/assets",
        "--include-data-dir=mood_readers/data=mood_readers/data",
        str(entry_point),
    ]

    cmd = common_args + _platform_icon_arg(base_dir)

    print("Starting Nuitka build...")
    try:
        subprocess.run(cmd, cwd=base_dir, check=True)
    except FileNotFoundError as exc:
        raise RuntimeError("Nuitka is not installed in this environment.") from exc

    # Do not copy .env into build outputs.
    # API keys should be sourced from OS keychain at runtime.
    print("Skipped .env copy for security. Use OS keychain or local runtime environment variables.")

    print("Nuitka build complete.")


if __name__ == "__main__":
    build()
