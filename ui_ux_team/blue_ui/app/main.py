import json
import re
import sys
import threading
import time
from pathlib import Path


# Ensure project root is importable when running directly.
if not getattr(sys, "frozen", False):
    project_root = Path(__file__).resolve().parents[3]
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))


def _runtime_base_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent

    argv0 = Path(sys.argv[0]).expanduser() if sys.argv and sys.argv[0] else None
    if argv0 is not None:
        try:
            return argv0.resolve().parent
        except Exception:
            pass
    return Path.cwd()


def _settings_path() -> Path:
    return _runtime_base_dir() / "config" / "app_config.json"


def _read_selected_theme_key() -> str:
    key_migration = {
        "vscode_dark": "dark_theme",
        "vscode_light": "light_theme",
    }
    try:
        with open(_settings_path(), "r", encoding="utf-8") as f:
            data = json.load(f)
        key = str((data or {}).get("selected_theme", "")).strip()
        key = key_migration.get(key, key)
        return key or "dark_theme"
    except Exception:
        return "dark_theme"


def _to_hex_color(value: str, fallback: str) -> str:
    c = str(value or "").strip()
    if c.startswith("#") and len(c) == 7:
        return c
    if c.startswith("#") and len(c) == 4:
        return f"#{c[1] * 2}{c[2] * 2}{c[3] * 2}"

    match = re.match(r"rgba?\(([^)]+)\)", c)
    if match:
        parts = [p.strip() for p in match.group(1).split(",")]
        if len(parts) >= 3:
            try:
                r = max(0, min(255, int(float(parts[0]))))
                g = max(0, min(255, int(float(parts[1]))))
                b = max(0, min(255, int(float(parts[2]))))
                return f"#{r:02X}{g:02X}{b:02X}"
            except Exception:
                pass
    return fallback


def _loader_palette(theme_key: str) -> dict[str, str]:
    fallback = {
        "bg": "#1E1E1E",
        "text": "#D4D4D4",
        "muted": "#A9B1BA",
        "accent": "#569CD6",
        "border": "#3C3C3C",
        "trough": "#2B2B2B",
    }
    try:
        from ui_ux_team.blue_ui.theme.palettes import DEFAULT_THEME_KEY, THEMES

        entry = THEMES.get(theme_key) or THEMES.get(DEFAULT_THEME_KEY) or {}
        t = entry.get("tokens", {})
        return {
            "bg": _to_hex_color(t.get("COLOR_BG_MAIN", fallback["bg"]), fallback["bg"]),
            "text": _to_hex_color(t.get("TEXT", fallback["text"]), fallback["text"]),
            "muted": _to_hex_color(t.get("TEXT_MUTED", fallback["muted"]), fallback["muted"]),
            "accent": _to_hex_color(t.get("PRIMARY", fallback["accent"]), fallback["accent"]),
            "border": _to_hex_color(t.get("BORDER_SUBTLE", fallback["border"]), fallback["border"]),
            "trough": _to_hex_color(t.get("BG_INPUT", fallback["trough"]), fallback["trough"]),
        }
    except Exception:
        return fallback


def _format_eta(seconds: float) -> str:
    s = max(0, int(round(seconds)))
    m, s = divmod(s, 60)
    h, m = divmod(m, 60)
    if h > 0:
        return f"{h:02d}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"


class _NullBootstrapLoader:
    def start(self, estimated_total_seconds: float, initial_status: str = "Starting app bootstrap...") -> None:
        return None

    def update_stage(self, status_text: str, progress: float) -> None:
        return None

    def smooth_pump(self, duration_s: float) -> None:
        return None

    def complete(self, status_text: str = "Launch ready") -> None:
        return None

    def close(self) -> None:
        return None


class _TkBootstrapLoader:
    def __init__(self, palette: dict[str, str]):
        import tkinter as tk
        from tkinter import ttk

        self._tk = tk
        self._root = tk.Tk()
        self._root.title("Starting DJ Blue")
        self._root.resizable(False, False)
        self._root.attributes("-topmost", True)
        self._root.configure(bg=palette["bg"])
        self._root.protocol("WM_DELETE_WINDOW", lambda: None)

        width = 560
        height = 220
        vroot_x = int(self._root.winfo_vrootx())
        vroot_y = int(self._root.winfo_vrooty())
        vroot_w = int(self._root.winfo_vrootwidth())
        vroot_h = int(self._root.winfo_vrootheight())

        pointer_x = int(self._root.winfo_pointerx())
        pointer_y = int(self._root.winfo_pointery())
        if pointer_x <= 0 and pointer_y <= 0:
            pointer_x = vroot_x + (vroot_w // 2)
            pointer_y = vroot_y + (vroot_h // 2)

        x = pointer_x - (width // 2)
        y = pointer_y - (height // 2)
        x = max(vroot_x, min(x, (vroot_x + vroot_w) - width))
        y = max(vroot_y, min(y, (vroot_y + vroot_h) - height))
        self._root.geometry(f"{width}x{height}+{x}+{y}")

        frame = tk.Frame(
            self._root,
            bg=palette["bg"],
            highlightbackground=palette["border"],
            highlightthickness=1,
            bd=0,
        )
        frame.pack(fill="both", expand=True, padx=8, pady=8)

        self._title_var = tk.StringVar(value="Launching DJ Blue")
        self._status_var = tk.StringVar(value="Starting app bootstrap...")
        self._eta_var = tk.StringVar(value="ETA: --:--")

        title = tk.Label(
            frame,
            textvariable=self._title_var,
            bg=palette["bg"],
            fg=palette["text"],
            font=("Segoe UI", 16, "bold"),
            anchor="w",
        )
        title.pack(fill="x", padx=14, pady=(14, 2))

        status = tk.Label(
            frame,
            textvariable=self._status_var,
            bg=palette["bg"],
            fg=palette["muted"],
            font=("Segoe UI", 11),
            anchor="w",
            justify="left",
            wraplength=520,
        )
        status.pack(fill="x", padx=14, pady=(2, 8))

        style = ttk.Style(self._root)
        try:
            style.theme_use("clam")
        except Exception:
            pass
        self._progress_style = "Bootstrap.Horizontal.TProgressbar"
        style.configure(
            self._progress_style,
            troughcolor=palette["trough"],
            background=palette["accent"],
            bordercolor=palette["border"],
            darkcolor=palette["accent"],
            lightcolor=palette["accent"],
            thickness=14,
        )

        self._bar = ttk.Progressbar(
            frame,
            orient="horizontal",
            mode="determinate",
            maximum=100.0,
            style=self._progress_style,
        )
        self._bar.pack(fill="x", padx=14, pady=(2, 8))

        eta = tk.Label(
            frame,
            textvariable=self._eta_var,
            bg=palette["bg"],
            fg=palette["text"],
            font=("Segoe UI", 10, "bold"),
            anchor="w",
        )
        eta.pack(fill="x", padx=14, pady=(0, 10))

        self._target_progress = 0.0
        self._display_progress = 0.0
        self._estimated_total_s = 6.0
        self._start_ts = time.perf_counter()
        self._closed = False

    def start(self, estimated_total_seconds: float, initial_status: str = "Starting app bootstrap...") -> None:
        self._estimated_total_s = max(1.0, float(estimated_total_seconds))
        self._start_ts = time.perf_counter()
        self._target_progress = 0.0
        self._display_progress = 0.0
        self._status_var.set(initial_status)
        self._eta_var.set("ETA: --:--")
        self._bar.configure(value=0.0)
        self._pump_once()

    def update_stage(self, status_text: str, progress: float) -> None:
        self._status_var.set(status_text)
        self._target_progress = max(0.0, min(100.0, float(progress)))
        self._animate_once()
        self._pump_once()

    def smooth_pump(self, duration_s: float) -> None:
        if self._closed:
            return
        end = time.perf_counter() + max(0.0, duration_s)
        while time.perf_counter() < end:
            self._animate_once()
            self._pump_once()
            time.sleep(0.016)

    def complete(self, status_text: str = "Launch ready") -> None:
        self._status_var.set(status_text)
        self._target_progress = 100.0
        self.smooth_pump(0.12)
        self._eta_var.set("ETA: 00:00")
        self._bar.configure(value=100.0)
        self._pump_once()

    def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        try:
            self._root.destroy()
        except Exception:
            pass

    def _animate_once(self) -> None:
        if self._closed:
            return
        delta = self._target_progress - self._display_progress
        if abs(delta) < 0.04:
            self._display_progress = self._target_progress
        else:
            self._display_progress += delta * 0.24

        self._bar.configure(value=self._display_progress)

        elapsed = max(0.001, time.perf_counter() - self._start_ts)
        if self._display_progress <= 0.1:
            eta_s = max(0.0, self._estimated_total_s - elapsed)
        else:
            by_rate = elapsed * ((100.0 - self._display_progress) / self._display_progress)
            by_plan = max(0.0, self._estimated_total_s - elapsed)
            eta_s = (0.65 * by_plan) + (0.35 * by_rate)
        self._eta_var.set(f"ETA: {_format_eta(eta_s)}")

    def _pump_once(self) -> None:
        if self._closed:
            return
        self._root.update_idletasks()
        self._root.update()


def _build_loader(theme_key: str):
    palette = _loader_palette(theme_key)
    try:
        return _TkBootstrapLoader(palette)
    except Exception:
        return _NullBootstrapLoader()


def run() -> int:
    selected_theme = _read_selected_theme_key()
    loader = _build_loader(selected_theme)

    boot_steps = [
        ("Loading configuration...", 0.5),
        ("Importing UI framework...", 1.6),
        ("Creating UI runtime...", 0.8),
        ("Loading application modules...", 1.2),
        ("Applying selected theme...", 0.7),
        ("Initializing services...", 2.0),
        ("Building main interface...", 2.6),
    ]
    total_weight = sum(weight for _, weight in boot_steps)
    completed_weight = 0.0

    loader.start(estimated_total_seconds=total_weight, initial_status="Starting app bootstrap...")
    loader.update_stage("Starting app bootstrap...", 0.8)
    loader.smooth_pump(0.05)

    qt_app_factory = None
    app = None
    composer_cls = None
    composer = None

    def _run_step(label: str, weight: float, action, *, async_mode: bool = False) -> None:
        nonlocal completed_weight
        step_start = (completed_weight / total_weight) * 100.0
        step_end = ((completed_weight + weight) / total_weight) * 100.0
        loader.update_stage(label, step_start)

        if async_mode:
            errors: list[BaseException] = []
            done = threading.Event()

            def _worker() -> None:
                try:
                    action()
                except BaseException as exc:
                    errors.append(exc)
                finally:
                    done.set()

            thread = threading.Thread(target=_worker, daemon=True)
            thread.start()

            # Planned slope keeps the bar moving smoothly from the first frames.
            started = time.perf_counter()
            expected_s = max(0.22, float(weight))
            while not done.is_set():
                elapsed = time.perf_counter() - started
                plan_ratio = min(0.94, elapsed / expected_s)
                target = step_start + ((step_end - step_start) * plan_ratio)
                loader.update_stage(label, target)
                loader.smooth_pump(0.016)

            thread.join()
            if errors:
                raise errors[0]
        else:
            action()

        completed_weight += weight
        loader.update_stage(label, step_end)
        loader.smooth_pump(0.035)

    from ui_ux_team.blue_ui.config import ensure_config_initialized

    _run_step("Loading configuration...", 0.5, ensure_config_initialized, async_mode=True)

    def _import_qt():
        nonlocal qt_app_factory
        from PySide6.QtWidgets import QApplication as _QApplication

        qt_app_factory = _QApplication

    _run_step("Importing UI framework...", 1.6, _import_qt, async_mode=True)
    if qt_app_factory is None:
        raise RuntimeError("Failed to import QApplication during startup.")

    def _create_qt_app():
        nonlocal app
        app = qt_app_factory(sys.argv)

    _run_step("Creating UI runtime...", 0.8, _create_qt_app)

    def _import_composer():
        nonlocal composer_cls
        from ui_ux_team.blue_ui.app.composition import AppComposer as _AppComposer

        composer_cls = _AppComposer

    _run_step("Loading application modules...", 1.2, _import_composer, async_mode=True)
    if composer_cls is None:
        raise RuntimeError("Failed to import AppComposer during startup.")

    from ui_ux_team.blue_ui.theme import ensure_default_theme

    _run_step("Applying selected theme...", 0.7, ensure_default_theme, async_mode=True)

    composer = composer_cls(auto_bootstrap=False)
    _run_step("Initializing services...", 2.0, composer.build_services, async_mode=True)
    _run_step("Building main interface...", 2.6, composer.build_window)

    loader.complete("Launch ready")
    loader.close()

    composer.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(run())
