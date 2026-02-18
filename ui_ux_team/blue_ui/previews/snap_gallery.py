"""
Batch snapshot and gallery generator for Blue UI themes.
Iterates through all themes and creates a stitched image of core windows in a box layout.
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

def _blue_ui_root() -> Path:
    return Path(__file__).resolve().parents[1]

def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]

# Core previews to include in the theme gallery
CORE_PREVIEWS = [
    {
        "module": "ui_ux_team.blue_ui.previews.preview_main_window",
        "class": "MainWindowPreview",
        "width": 1000, "height": 700, "name": "main"
    },
    {
        "module": "ui_ux_team.blue_ui.previews.preview_transcript_window",
        "class": "TranscriptWindowPreview",
        "width": 500, "height": 700, "name": "transcript"
    },
    {
        "module": "ui_ux_team.blue_ui.previews.preview_chat_window",
        "class": "BlueBirdChatPreview",
        "width": 420, "height": 640, "name": "chat"
    },
    {
        "module": "ui_ux_team.blue_ui.previews.preview_profile_window",
        "class": "ProfileWindowPreview",
        "width": 380, "height": 460, "name": "profile"
    },
]

SETTINGS_TABS = [
    "Recording Sources",
    "Theme Selection",
    "Music Library",
    "API Usage Limits"
]

def run_cmd(cmd: list[str], env_extra: dict = None):
    env = os.environ.copy()
    if env_extra:
        env.update(env_extra)
    subprocess.run(cmd, check=True, env=env)

def generate_gallery(theme_key: str, subfolder: str, output_root: Path):
    temp_snaps = []
    theme_snap_dir = output_root / subfolder / "temp" / theme_key
    theme_snap_dir.mkdir(parents=True, exist_ok=True)

    # 1. Capture basic core previews
    for preview in CORE_PREVIEWS:
        out_path = theme_snap_dir / f"{preview['name']}.png"
        cmd = [
            sys.executable, str(_blue_ui_root() / "previews" / "ui_iterate.py"), "snap",
            "--module", preview["module"],
            "--class-name", preview["class"],
            "--width", str(preview["width"]), "--height", str(preview["height"]),
            "--theme", theme_key, "--offscreen", "--out", str(out_path)
        ]
        run_cmd(cmd)
        temp_snaps.append(out_path)

    # 2. Capture all settings tabs
    for tab in SETTINGS_TABS:
        safe_tab = tab.lower().replace(" ", "_")
        out_path = theme_snap_dir / f"settings_{safe_tab}.png"
        cmd = [
            sys.executable, str(_blue_ui_root() / "previews" / "ui_iterate.py"), "snap",
            "--module", "ui_ux_team.blue_ui.previews.preview_settings_popup",
            "--class-name", "SettingsPopupPreview",
            "--width", "600", "--height", "450",
            "--theme", theme_key, "--offscreen", "--out", str(out_path)
        ]
        run_cmd(cmd, env_extra={"DJ_BLUE_SETTINGS_TAB": tab})
        temp_snaps.append(out_path)

    # 3. Stitch them together in a BOX layout (2 columns)
    images = [Image.open(p) for p in temp_snaps]
    
    # Calculate grid
    cols = 2
    rows = (len(images) + 1) // cols
    
    # Calculate max dimensions per cell
    max_w = max(img.width for img in images)
    max_h = max(img.height for img in images)
    
    padding = 40
    gallery_w = (max_w * cols) + (padding * (cols + 1))
    gallery_h = (max_h * rows) + (padding * (rows + 1)) + 100 # + label space
    
    # Use RGBA for transparency
    gallery_img = Image.new('RGBA', (gallery_w, gallery_h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(gallery_img)
    
    # Add Title
    try:
        # Try to find a system font
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 48)
    except:
        font = ImageFont.load_default()
        
    draw.text((padding, 20), f"Blue UI Theme Gallery: {theme_key}", fill=(200, 200, 200), font=font)

    for i, img in enumerate(images):
        col = i % cols
        row = i // cols
        
        # Center image within its cell
        x = padding + col * (max_w + padding) + (max_w - img.width) // 2
        y = 100 + padding + row * (max_h + padding) + (max_h - img.height) // 2
        
        # Draw cell border
        draw.rectangle(
            [padding + col * (max_w + padding) - 5, 100 + padding + row * (max_h + padding) - 5,
             padding + col * (max_w + padding) + max_w + 5, 100 + padding + row * (max_h + padding) + max_h + 5],
            outline=(60, 60, 70), width=2
        )
        
        gallery_img.paste(img, (x, y))
        
    final_path = output_root / subfolder / f"gallery_{theme_key}.png"
    gallery_img.save(final_path)
    print(f"✅ Box Gallery saved for {theme_key}: {final_path}")

def main():
    parser = argparse.ArgumentParser(description="Batch snapshot tool.")
    parser.add_argument("--subfolder", default="audit_grid", help="Subfolder under .snapshots")
    parser.add_argument("--theme", default="", help="Specific theme to run (default: all)")
    args = parser.parse_args()

    os.environ["PYTHONPATH"] = str(_repo_root())
    output_root = _blue_ui_root() / "previews" / ".snapshots"
    
    sys.path.insert(0, str(_repo_root()))
    from ui_ux_team.blue_ui.theme.palettes import THEMES
    
    target_themes = [args.theme] if args.theme else list(THEMES.keys())
    
    for theme in target_themes:
        print(f"\n--- Generating Box Gallery for Theme: {theme} ---")
        generate_gallery(theme, args.subfolder, output_root)

if __name__ == "__main__":
    main()
