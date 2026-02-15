import os
import platform
import shutil
import stat
import subprocess
from pathlib import Path


APP_NAME = "dj-blue-ai"


def _arch() -> str:
    machine = platform.machine().lower()
    if machine in {"x86_64", "amd64"}:
        return "x86_64"
    if machine in {"aarch64", "arm64"}:
        return "aarch64"
    return machine or "unknown"


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _make_executable(path: Path) -> None:
    mode = path.stat().st_mode
    path.chmod(mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


def _resolve_appimagetool(base_dir: Path) -> str:
    from_env = os.environ.get("APPIMAGETOOL", "").strip()
    if from_env:
        return from_env
    local_tool = base_dir / "tools" / "appimagetool.AppImage"
    if local_tool.exists():
        return str(local_tool)
    which = shutil.which("appimagetool")
    if which:
        return which
    raise FileNotFoundError(
        "appimagetool not found. Set APPIMAGETOOL=/path/to/appimagetool.AppImage or install appimagetool."
    )


def build() -> None:
    base_dir = Path(__file__).resolve().parent
    src_binary = base_dir / "dist" / APP_NAME
    if not src_binary.exists():
        raise FileNotFoundError(f"Missing PyInstaller binary: {src_binary}. Run build_binary.py first.")

    icon_src = base_dir / "ui_ux_team" / "assets" / "app_icons" / "linux" / "512.png"
    if not icon_src.exists():
        raise FileNotFoundError(f"Missing Linux icon: {icon_src}")

    appdir = base_dir / "build" / "appimage" / "AppDir"
    out_path = base_dir / "dist" / f"{APP_NAME}-linux-{_arch()}.AppImage"

    if appdir.exists():
        shutil.rmtree(appdir)
    if out_path.exists():
        out_path.unlink()

    (appdir / "usr" / "bin").mkdir(parents=True, exist_ok=True)
    (appdir / "usr" / "share" / "icons" / "hicolor" / "512x512" / "apps").mkdir(parents=True, exist_ok=True)

    app_bin = appdir / "usr" / "bin" / APP_NAME
    shutil.copy2(src_binary, app_bin)
    _make_executable(app_bin)

    root_icon = appdir / f"{APP_NAME}.png"
    share_icon = appdir / "usr" / "share" / "icons" / "hicolor" / "512x512" / "apps" / f"{APP_NAME}.png"
    shutil.copy2(icon_src, root_icon)
    shutil.copy2(icon_src, share_icon)

    apprun = appdir / "AppRun"
    _write_text(
        apprun,
        "#!/bin/sh\n"
        'HERE="$(dirname "$(readlink -f "$0")")"\n'
        f'exec "$HERE/usr/bin/{APP_NAME}" "$@"\n',
    )
    _make_executable(apprun)

    desktop = appdir / f"{APP_NAME}.desktop"
    _write_text(
        desktop,
        "[Desktop Entry]\n"
        "Type=Application\n"
        "Name=DJ Blue AI\n"
        f"Exec={APP_NAME}\n"
        f"Icon={APP_NAME}\n"
        "Terminal=false\n"
        "Categories=AudioVideo;Audio;Utility;\n",
    )

    appimagetool = _resolve_appimagetool(base_dir)
    env = os.environ.copy()
    env["APPIMAGE_EXTRACT_AND_RUN"] = "1"
    env.setdefault("ARCH", _arch())

    cmd = [appimagetool, str(appdir), str(out_path)]
    print("Building AppImage...")
    subprocess.run(cmd, cwd=base_dir, check=True, env=env)
    print(f"AppImage created: {out_path}")


if __name__ == "__main__":
    build()
