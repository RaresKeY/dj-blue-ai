import argparse
import importlib
import inspect
import os
import re
import sys
import time
from pathlib import Path


def _snake_case(name: str) -> str:
    raw = re.sub(r"[^a-zA-Z0-9_]+", "_", (name or "").strip())
    raw = re.sub(r"_+", "_", raw).strip("_").lower()
    return raw or "ui_test_component"


def _camel_case(snake_name: str) -> str:
    return "".join(part.capitalize() for part in snake_name.split("_") if part) or "UiTestComponent"


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _blue_ui_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _ensure_project_root_on_path() -> None:
    root = _repo_root()
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))


def _component_template(class_name: str) -> str:
    return f"""from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QFrame, QHBoxLayout, QVBoxLayout, QWidget


def _box(name: str, bg: str, border: str = "#FFFFFF", min_h: int = 30) -> QFrame:
    frame = QFrame()
    frame.setObjectName(name)
    frame.setMinimumHeight(min_h)
    frame.setStyleSheet(
        f\"\"\"
        QFrame {{
            background: {{bg}};
            border: 1px solid {{border}};
            border-radius: 6px;
        }}
        QLabel {{
            color: #FFFFFF;
            font-size: 11px;
            font-weight: 700;
            background: transparent;
            border: none;
        }}
        \"\"\"
    )
    layout = QVBoxLayout(frame)
    layout.setContentsMargins(6, 4, 6, 4)
    label = QLabel(name)
    label.setAlignment(Qt.AlignCenter)
    layout.addWidget(label)
    return frame


class {class_name}(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("{class_name}")
        self.setMinimumSize(760, 360)

        root = QVBoxLayout(self)
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(8)

        top = _box("TOP", "#2C3E50", border="#8BB7FF", min_h=180)
        bottom = _box("BOTTOM", "#3B2F46", border="#D2A8FF", min_h=80)
        root.addWidget(top, 1)
        root.addWidget(bottom, 0)

        top_layout = QHBoxLayout(top)
        top_layout.setContentsMargins(8, 8, 8, 8)
        top_layout.setSpacing(6)
        top_layout.addWidget(_box("LEFT_SLOT", "#315A7D", border="#9FD6FF", min_h=100))
        top_layout.addWidget(_box("CENTER_SLOT", "#5A3D7D", border="#DDB9FF", min_h=120))
        top_layout.addWidget(_box("RIGHT_SLOT", "#315A7D", border="#9FD6FF", min_h=100))
"""


def _preview_template(component_module: str, class_name: str, preview_class_name: str) -> str:
    return f"""import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication, QVBoxLayout, QWidget

project_root = Path(__file__).resolve()
while project_root.name != "ui_ux_team" and project_root != project_root.parent:
    project_root = project_root.parent
project_root = project_root.parent if project_root.name == "ui_ux_team" else Path(__file__).resolve().parents[3]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from ui_ux_team.blue_ui.theme import ensure_default_theme
from {component_module} import {class_name}


class {preview_class_name}(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("{preview_class_name}")
        self.resize(900, 560)

        root = QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)
        root.addWidget({class_name}(), 1)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    ensure_default_theme()
    window = {preview_class_name}()
    window.show()
    raise SystemExit(app.exec())
"""


def _write_text(path: Path, text: str, force: bool) -> None:
    if path.exists() and not force:
        raise FileExistsError(f"File already exists: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _normalize_rel_dir(raw: str, default_rel: str) -> Path:
    cleaned = str(raw or "").strip().replace("\\", "/").strip("/")
    return Path(cleaned) if cleaned else Path(default_rel)


def _ensure_package_tree(base_dir: Path, rel_dir: Path) -> None:
    current = base_dir
    for part in rel_dir.parts:
        current = current / part
        current.mkdir(parents=True, exist_ok=True)
        init_file = current / "__init__.py"
        if not init_file.exists():
            init_file.write_text("", encoding="utf-8")


def _module_from_rel(rel_dir: Path, leaf_module: str) -> str:
    parts = ["ui_ux_team", "blue_ui"] + list(rel_dir.parts) + [leaf_module]
    return ".".join(parts)


def cmd_scaffold(args: argparse.Namespace) -> int:
    _ensure_project_root_on_path()
    blue_ui = _blue_ui_root()
    component_rel = _normalize_rel_dir(args.component_rel, "tests/iteration/dev")
    preview_rel = _normalize_rel_dir(args.preview_rel, "previews/iteration")
    component_dir = blue_ui / component_rel
    preview_dir = blue_ui / preview_rel

    _ensure_package_tree(blue_ui, component_rel)
    _ensure_package_tree(blue_ui, preview_rel)

    name = _snake_case(args.name)
    comp_class = f"{_camel_case(name)}TestComponent"
    preview_class = f"{_camel_case(name)}Preview"

    component_path = component_dir / f"{name}.py"
    preview_path = preview_dir / f"preview_{name}.py"

    component_module = _module_from_rel(component_rel, name)
    preview_module = _module_from_rel(preview_rel, f"preview_{name}")
    component_code = _component_template(comp_class)
    preview_code = _preview_template(component_module, comp_class, preview_class)

    _write_text(component_path, component_code, force=args.force)
    _write_text(preview_path, preview_code, force=args.force)

    print(f"[ui_iterate] created component: {component_path}")
    print(f"[ui_iterate] created preview:   {preview_path}")
    print(f"[ui_iterate] run preview: python3 {preview_path}")
    print(f"[ui_iterate] preview module: {preview_module}")
    print(
        "[ui_iterate] snapshot example: "
        f"python3 ui_ux_team/blue_ui/previews/ui_iterate.py snap --module "
        f"{preview_module} --class-name {preview_class}"
    )
    return 0


def _resolve_widget_class(module, class_name: str | None):
    from PySide6.QtWidgets import QWidget

    if class_name:
        cls = getattr(module, class_name, None)
        if cls is None:
            raise AttributeError(f"Class '{class_name}' not found in module {module.__name__}")
        if not inspect.isclass(cls) or not issubclass(cls, QWidget):
            raise TypeError(f"Class '{class_name}' is not a QWidget subclass")
        return cls

    candidates = []
    for _, obj in inspect.getmembers(module, inspect.isclass):
        if issubclass(obj, QWidget) and obj is not QWidget and obj.__module__ == module.__name__:
            candidates.append(obj)
    if not candidates:
        raise RuntimeError(f"No QWidget subclass found in module {module.__name__}")
    preview_named = [c for c in candidates if "Preview" in c.__name__]
    return preview_named[0] if preview_named else candidates[0]


def _make_snapshot_path(module_name: str, class_name: str) -> Path:
    ts = time.strftime("%Y%m%d_%H%M%S")
    out_dir = _blue_ui_root() / "previews" / ".snapshots"
    out_dir.mkdir(parents=True, exist_ok=True)
    safe_module = module_name.split(".")[-1]
    safe_class = _snake_case(class_name)
    return out_dir / f"{safe_module}_{safe_class}_{ts}.png"


def cmd_snap(args: argparse.Namespace) -> int:
    _ensure_project_root_on_path()
    if args.offscreen:
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

    try:
        from PySide6.QtWidgets import QApplication, QWidget
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "PySide6 is required for `ui_iterate.py snap`. Install dependencies first "
            "(for example: `pip install -r requirements.txt`)."
        ) from exc

    app = QApplication.instance() or QApplication(sys.argv)

    if args.apply_theme:
        try:
            from ui_ux_team.blue_ui.theme import ensure_default_theme

            ensure_default_theme()
        except Exception:
            pass

    module = importlib.import_module(args.module)
    widget_cls = _resolve_widget_class(module, args.class_name)
    widget = widget_cls()
    if args.width > 0 and args.height > 0:
        widget.resize(args.width, args.height)

    widget.show()
    widget.raise_()

    end = time.perf_counter() + (max(0, int(args.delay_ms)) / 1000.0)
    while time.perf_counter() < end:
        app.processEvents()
        time.sleep(0.016)

    target: QWidget = widget
    if args.object_name:
        child = widget.findChild(QWidget, args.object_name)
        if child is None:
            raise RuntimeError(f"objectName '{args.object_name}' not found in {widget_cls.__name__}")
        target = child

    out_path = Path(args.out).expanduser() if args.out else _make_snapshot_path(args.module, widget_cls.__name__)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    ok = target.grab().save(str(out_path))
    widget.close()
    app.processEvents()
    if not ok:
        raise RuntimeError(f"Failed to save screenshot to {out_path}")
    print(f"[ui_iterate] screenshot saved: {out_path}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="UI iterative workflow helper for Blue UI components.")
    sub = parser.add_subparsers(dest="cmd", required=True)

    scaffold = sub.add_parser("scaffold", help="Create a test component + preview boilerplate.")
    scaffold.add_argument("name", help="Component name (snake/camel/slug accepted).")
    scaffold.add_argument(
        "--component-rel",
        default="tests/iteration/dev",
        help="Component directory relative to ui_ux_team/blue_ui (default: tests/iteration/dev).",
    )
    scaffold.add_argument(
        "--preview-rel",
        default="previews/iteration",
        help="Preview directory relative to ui_ux_team/blue_ui (default: previews/iteration).",
    )
    scaffold.add_argument("--force", action="store_true", help="Overwrite generated files if they exist.")
    scaffold.set_defaults(func=cmd_scaffold)

    snap = sub.add_parser("snap", help="Render a QWidget preview/component and save a screenshot.")
    snap.add_argument("--module", required=True, help="Python module path (e.g. ui_ux_team.blue_ui.previews.preview_x).")
    snap.add_argument("--class-name", default="", help="Widget class name in module. Auto-detected if omitted.")
    snap.add_argument("--object-name", default="", help="Optional child objectName to snapshot instead of root widget.")
    snap.add_argument("--out", default="", help="Output PNG path. Defaults to previews/.snapshots timestamp file.")
    snap.add_argument("--width", type=int, default=0, help="Optional resize width before screenshot.")
    snap.add_argument("--height", type=int, default=0, help="Optional resize height before screenshot.")
    snap.add_argument("--delay-ms", type=int, default=260, help="Wait time before capture (default: 260ms).")
    snap.add_argument("--offscreen", action="store_true", help="Set QT_QPA_PLATFORM=offscreen for headless captures.")
    snap.add_argument("--no-theme", action="store_true", help="Skip ensure_default_theme() before rendering.")
    snap.set_defaults(func=cmd_snap)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    args.apply_theme = not getattr(args, "no_theme", False)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
