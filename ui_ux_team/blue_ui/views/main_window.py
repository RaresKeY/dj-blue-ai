import json
import os
import random
import sys
import time
from pathlib import Path

from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QPalette, QColor, QPixmap, QFont, QIcon
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from architects.helpers.managed_mem import ManagedMem
from architects.helpers.miniaudio_player import MiniaudioPlayer
from architects.helpers.resource_path import resource_path
from architects.helpers.tabs_audio import get_display_names
from architects.helpers.transcription_manager import TranscriptionManager
from ui_ux_team.blue_ui.config import default_music_folder, get_setting, set_setting
from ui_ux_team.blue_ui.theme import set_theme
from ui_ux_team.blue_ui.theme.native_window import apply_native_titlebar_for_theme
from ui_ux_team.blue_ui.theme import tokens as theme_tokens
from ui_ux_team.blue_ui.views.chat_window import BlueBirdChatView
from ui_ux_team.blue_ui.views.settings_popup import FloatingMenu, SettingsPopup
from ui_ux_team.blue_ui.views.transcript_window import TranscriptWindowView
from ui_ux_team.blue_ui.widgets.image_button import ImageButton, IMAGE_NOT_FOUND
from ui_ux_team.blue_ui.widgets.marquee import QueuedMarqueeLabel
from ui_ux_team.blue_ui.widgets.song_cover_carousel import SongCoverCarousel
from ui_ux_team.blue_ui.widgets.theme_chooser import ThemeChooserMenu
from ui_ux_team.blue_ui.widgets.timeline import PlaybackTimeline
from ui_ux_team.blue_ui.widgets.toast import FloatingToast
from ui_ux_team.blue_ui.widgets.volume import IntegratedVolumeControl


def get_project_root() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parents[3]


BASE = resource_path("ui_ux_team/assets")
T_CHUNK = 30


def _icon_relative_candidates() -> list[str]:
    if sys.platform.startswith("win"):
        platform_first = "ui_ux_team/assets/app_icons/windows/dj-blue-ai.ico"
    elif sys.platform == "darwin":
        platform_first = "ui_ux_team/assets/app_icons/macos/dj-blue-ai.icns"
    else:
        platform_first = "ui_ux_team/assets/app_icons/linux/512.png"
    return [
        platform_first,
        "ui_ux_team/assets/app_icons/linux/512.png",
        "ui_ux_team/assets/logo_margins.png",
    ]


def _resolve_window_icon() -> QIcon | None:
    app = QApplication.instance()
    if app is not None:
        inherited = app.windowIcon()
        if inherited is not None and not inherited.isNull():
            return inherited

    for rel in _icon_relative_candidates():
        candidate = resource_path(rel)
        if not os.path.exists(candidate):
            continue
        icon = QIcon(candidate)
        if not icon.isNull():
            return icon
    return None


def _parse_color(value: str, fallback: str) -> QColor:
    color = QColor((value or "").strip())
    if color.isValid():
        return color
    fallback_color = QColor(fallback)
    if fallback_color.isValid():
        return fallback_color
    return QColor("#FFFFFF")


def _color_with_alpha(value: str, alpha: float, fallback: str) -> str:
    c = _parse_color(value, fallback)
    a = max(0.0, min(1.0, float(alpha)))
    return f"rgba({c.red()}, {c.green()}, {c.blue()}, {a:.3f})"


def _contrast_ratio(fg: QColor, bg: QColor) -> float:
    def channel(v: int) -> float:
        c = float(v) / 255.0
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4

    def luminance(color: QColor) -> float:
        return (
            0.2126 * channel(color.red())
            + 0.7152 * channel(color.green())
            + 0.0722 * channel(color.blue())
        )

    l1 = luminance(fg)
    l2 = luminance(bg)
    lighter = max(l1, l2)
    darker = min(l1, l2)
    return (lighter + 0.05) / (darker + 0.05)


def _resolve_contrast_text(bg_color: str, preferred_text: str, minimum_ratio: float = 4.5) -> str:
    bg = _parse_color(bg_color, "#1E1E1E")
    preferred = _parse_color(preferred_text, "#D4D4D4")
    if _contrast_ratio(preferred, bg) >= minimum_ratio:
        return preferred.name()
    white = QColor("#FFFFFF")
    black = QColor("#000000")
    return white.name() if _contrast_ratio(white, bg) >= _contrast_ratio(black, bg) else black.name()


class MainUI(QWidget):
    transcript_ready = Signal(dict)
    _AUDIO_EXTS = {".wav", ".mp3", ".flac", ".ogg", ".m4a", ".aac"}

    def __init__(self):
        super().__init__()
        self.setWindowTitle("DJ Blue UI")
        icon = _resolve_window_icon()
        if icon is not None:
            self.setWindowIcon(icon)
        self.resize(721, 487)
        apply_native_titlebar_for_theme(self)

        self._play_btn = None
        self._player = None
        self._paused = False
        self._currently_playing = "deep_purple_smoke_on_the_water.wav"
        self._current_volume = 0.8
        self._bluebird_chat = None
        self._settings_menu = None
        self._meet_type = None
        self._volume_control = None
        self._btn_transcript = None
        self._btn_api = None
        self._btn_info = None
        self._btn_meet_type = None
        self._btn_user = None
        self._btn_settings = None
        self._btn_prev = None
        self._btn_next = None
        self._btn_bluebird = None
        self._cover_carousel = None
        self._timeline = None
        self._timeline_dummy_duration = 240.0
        self._timeline_dummy_position = 0.0
        self._timeline_seek_lock_until = 0.0
        self._timeline_timer = QTimer(self)
        self._timeline_timer.setInterval(120)
        self._timeline_timer.timeout.connect(self._sync_timeline_from_player)
        self._timeline_timer.start()

        self.transcription_manager = None
        self.transcript_line = 0
        self._music_folder = self._load_music_folder_setting()
        self._music_path_edit = None
        self._music_empty_popup = None
        self._startup_preflight_shown = False
        self._startup_cycle_popup = None

        self.root = QVBoxLayout(self)
        self.root.setContentsMargins(0, 0, 0, 0)
        self.root.addWidget(self.build_main_layout())

        self.man_mem = ManagedMem()
        self._music_folder.mkdir(parents=True, exist_ok=True)

        mood_data_path = resource_path("mood_readers/data/mood_playlists_organized.json")
        with open(mood_data_path, "r", encoding="utf-8") as f:
            self.mood_map = json.load(f)

        self._transcript_win = TranscriptWindowView()
        self._transcript_win.closed.connect(lambda: setattr(self, "_show_transcript_window", False))
        self._transcript_win.record_clicked.connect(self.record_transcript)
        self._show_transcript_window = False

        self._current_session_segments = []
        self._current_session = f"SESSION [{self.man_mem.timestamp_helper()}]"

        self.transcript_ready.connect(self.handle_transcript_data)

        api_key = self.load_api_key()
        if api_key:
            self.transcription_manager = TranscriptionManager(api_key, chunk_seconds=T_CHUNK)
            self.transcription_manager.set_callback(self.transcript_ready.emit)
        else:
            print("Missing API Key, TranscriptionManager not initialized")
        QTimer.singleShot(600, self._show_start_cycle_popup_once)

    def basic_music_play(self, music_path):
        real_path = self._resolve_music_path(music_path)
        if real_path is None:
            print(f"Music file not found for input: {music_path}")
            self._play_btn.set_image("assets/play.png")
            return

        if self._player and self._currently_playing == music_path and self._player.is_playing():
            return

        self._currently_playing = music_path
        started = self._start_player(real_path)
        self._play_btn.set_image("assets/pause.png" if started else "assets/play.png")

    def _default_music_folder(self) -> Path:
        return default_music_folder()

    def _load_music_folder_setting(self) -> Path:
        stored = str(get_setting("music_folder", "")).strip()
        candidate = Path(stored).expanduser() if stored else self._default_music_folder()
        if not candidate.exists():
            candidate = self._default_music_folder()
        candidate.mkdir(parents=True, exist_ok=True)
        self._save_music_folder_setting(candidate)
        return candidate

    def _save_music_folder_setting(self, folder: Path) -> None:
        set_setting("music_folder", str(folder.resolve()))

    @staticmethod
    def _has_audio_files(folder: Path) -> bool:
        try:
            for p in folder.iterdir():
                if p.is_file() and p.suffix.lower() in MainUI._AUDIO_EXTS:
                    return True
        except Exception:
            return False
        return False

    def _first_audio_file(self, folder: Path) -> Path | None:
        try:
            files = sorted(
                [p for p in folder.iterdir() if p.is_file() and p.suffix.lower() in self._AUDIO_EXTS],
                key=lambda p: p.name.lower(),
            )
            return files[0] if files else None
        except Exception:
            return None

    def _required_playlist_filenames(self) -> set[str]:
        required: set[str] = set()
        mood_map = getattr(self, "mood_map", None)
        if not isinstance(mood_map, dict):
            return required
        for tracks in mood_map.values():
            if not isinstance(tracks, list):
                continue
            for track in tracks:
                raw = str(track or "").strip()
                if not raw:
                    continue
                clean = raw[2:] if raw.startswith("./") else raw
                name = Path(clean).name
                if name:
                    required.add(name)
        return required

    def _music_collection_filenames(self) -> set[str]:
        names: set[str] = set()
        try:
            for p in self._music_folder.iterdir():
                if p.is_file() and p.suffix.lower() in self._AUDIO_EXTS:
                    names.add(p.name)
        except Exception:
            return set()
        return names

    def _music_tracks(self) -> list[Path]:
        try:
            return sorted(
                [p for p in self._music_folder.iterdir() if p.is_file() and p.suffix.lower() in self._AUDIO_EXTS],
                key=lambda p: p.name.lower(),
            )
        except Exception:
            return []

    def _missing_playlist_files(self) -> list[str]:
        required = self._required_playlist_filenames()
        if not required:
            return []
        available = self._music_collection_filenames()
        return sorted(required - available, key=str.lower)

    def _show_start_cycle_popup_once(self):
        if self._startup_preflight_shown:
            return
        self._startup_preflight_shown = True
        if os.environ.get("QT_QPA_PLATFORM", "").lower() == "offscreen":
            return
        self._show_start_cycle_popup()

    def _show_start_cycle_popup(self):
        if self._startup_cycle_popup is not None and self._startup_cycle_popup.isVisible():
            self._startup_cycle_popup.raise_()
            self._startup_cycle_popup.activateWindow()
            return

        api_ok = self.transcription_manager is not None
        music_non_empty = self._has_audio_files(self._music_folder)
        missing_playlist_files = self._missing_playlist_files()
        playlist_match_ok = len(missing_playlist_files) == 0
        can_start_cycle = api_ok and music_non_empty and playlist_match_ok
        popup_bg = getattr(theme_tokens, "COLOR_BG_MAIN", getattr(theme_tokens, "BACKGROUND", "#1E1E1E"))
        title_color = _resolve_contrast_text(popup_bg, getattr(theme_tokens, "TEXT_PRIMARY", "#D4D4D4"), 4.5)
        body_color = _resolve_contrast_text(popup_bg, getattr(theme_tokens, "TEXT_MUTED", "#A9B1BA"), 4.5)
        status_bg = _color_with_alpha(getattr(theme_tokens, "BG_INPUT", "#252526"), 0.92, "#252526")
        btn_fg = getattr(theme_tokens, "ACCENT", "#FF9B54")
        btn_bg = _color_with_alpha(btn_fg, 0.14, "#FF9B54")
        btn_bg_hover = _color_with_alpha(btn_fg, 0.24, "#FF9B54")
        btn_border = _color_with_alpha(btn_fg, 0.62, "#FF9B54")
        btn_disabled = _color_with_alpha(btn_fg, 0.45, "#FF9B54")

        popup = QDialog(self)
        popup.setWindowTitle("Start Recording/Playback Cycle")
        popup.setModal(True)
        popup.setMinimumWidth(680)

        root = QVBoxLayout(popup)
        root.setContentsMargins(16, 14, 16, 14)
        root.setSpacing(10)

        title = QLabel("Start recording/playback cycle?")
        title.setStyleSheet(f"color: {title_color}; font-size: 18px; font-weight: 700;")
        intro = QLabel(
            "The app requires API key, non-empty music collection, and full playlist file match "
            "with mood_readers/data/mood_playlists_organized.json."
        )
        intro.setWordWrap(True)
        intro.setStyleSheet(f"color: {body_color}; font-size: 13px;")

        def _status_html(is_ok: bool, text: str) -> str:
            icon = "✅" if is_ok else "❌"
            state = "OK" if is_ok else "WARN"
            return f"<div><b>{icon} {state}: {text}</b></div>"

        status_html = "".join(
            [
                _status_html(api_ok, "API key configured"),
                _status_html(music_non_empty, "Music collection has audio files"),
                _status_html(
                    playlist_match_ok,
                    "Music collection matches mood_playlists_organized.json",
                ),
            ]
        )
        status_label = QLabel(status_html)
        status_label.setWordWrap(True)
        status_label.setTextFormat(Qt.RichText)
        status_label.setStyleSheet(
            f"""
            color: {title_color};
            font-size: 14px;
            font-weight: 700;
            background: {status_bg};
            border: 1px solid {theme_tokens.BORDER_SUBTLE};
            border-radius: 10px;
            padding: 10px;
            """
        )

        detail_lines: list[str] = []
        if not api_ok:
            detail_lines.append("- Missing AI_STUDIO_API_KEY (keyring/.env).")
        if not music_non_empty:
            detail_lines.append(f"- Music folder is empty: {self._music_folder}")
        if not playlist_match_ok:
            sample = ", ".join(missing_playlist_files[:8])
            remaining = len(missing_playlist_files) - min(8, len(missing_playlist_files))
            suffix = f" (+{remaining} more)" if remaining > 0 else ""
            detail_lines.append(
                f"- Missing {len(missing_playlist_files)} required playlist file(s): {sample}{suffix}"
            )

        details = QLabel("\n".join(detail_lines) if detail_lines else "All requirements are satisfied.")
        details.setWordWrap(True)
        details.setStyleSheet(f"color: {body_color}; font-size: 13px;")

        start_btn = QPushButton("Start cycle")
        start_btn.setEnabled(can_start_cycle)
        if not can_start_cycle:
            start_btn.setToolTip("Fix warnings before starting cycle.")
        start_btn.clicked.connect(lambda: (popup.accept(), self._start_record_playback_cycle()))

        settings_btn = QPushButton("Open Settings")
        settings_btn.clicked.connect(lambda: (popup.accept(), self.settings_menu()))

        later_btn = QPushButton("Not now")
        later_btn.clicked.connect(popup.reject)

        buttons = QHBoxLayout()
        buttons.addStretch(1)
        buttons.addWidget(settings_btn)
        buttons.addWidget(later_btn)
        buttons.addWidget(start_btn)

        root.addWidget(title)
        root.addWidget(intro)
        root.addWidget(status_label)
        root.addWidget(details)
        root.addLayout(buttons)

        popup.setStyleSheet(
            f"""
            QDialog {{
                background: {popup_bg};
                border: 1px solid {theme_tokens.BORDER_SUBTLE};
                border-radius: 0px;
            }}
            QPushButton {{
                background: {btn_bg};
                color: {btn_fg};
                border: 1px solid {btn_border};
                border-radius: 8px;
                padding: 8px 14px;
                font-weight: 600;
                min-width: 110px;
            }}
            QPushButton:hover {{
                background: {btn_bg_hover};
            }}
            QPushButton:disabled {{
                background: {btn_bg};
                color: {btn_disabled};
                border: 1px solid {btn_disabled};
            }}
            """
        )
        popup.adjustSize()
        required_h = popup.sizeHint().height()
        required_w = popup.sizeHint().width()
        popup.setMinimumHeight(max(popup.minimumHeight(), required_h))
        popup.resize(max(popup.minimumWidth(), required_w), max(popup.minimumHeight(), required_h))
        popup.finished.connect(lambda *_: setattr(self, "_startup_cycle_popup", None))
        self._startup_cycle_popup = popup
        popup.open()

    def _start_record_playback_cycle(self):
        if not self._show_transcript_window:
            self.open_transcript()
        self.record_transcript()

    def _notify_if_music_folder_empty(self):
        if self._has_audio_files(self._music_folder):
            return
        msg = f"Music folder is empty: {self._music_folder}. Add audio files to enable playback."
        print(msg)
        self._show_music_folder_empty_popup()

    def _show_music_folder_empty_popup(self):
        if self._music_empty_popup is not None and self._music_empty_popup.isVisible():
            self._music_empty_popup.raise_()
            self._music_empty_popup.activateWindow()
            return

        popup = QDialog(self)
        popup.setWindowTitle("Music Library")
        popup.setModal(True)
        popup.setMinimumWidth(460)

        root = QVBoxLayout(popup)
        root.setContentsMargins(16, 14, 16, 14)
        root.setSpacing(10)

        title = QLabel("Music folder is empty")
        title.setStyleSheet(f"color: {theme_tokens.TEXT_PRIMARY}; font-size: 17px; font-weight: 700;")
        body = QLabel(
            f"Add audio files (.wav/.mp3/.flac/.ogg/.m4a/.aac) to:\n{self._music_folder}"
        )
        body.setWordWrap(True)
        body.setStyleSheet(f"color: {theme_tokens.TEXT_MUTED}; font-size: 13px;")

        close_btn = QPushButton("OK")
        close_btn.clicked.connect(popup.accept)
        close_btn.setStyleSheet(
            """
            QPushButton {
                background: rgba(255, 138, 61, 0.14);
                color: #FF8A3D;
                border: 1px solid rgba(255, 138, 61, 0.62);
                border-radius: 8px;
                padding: 8px 18px;
                font-weight: 600;
                min-width: 90px;
            }
            QPushButton:hover {
                background: rgba(255, 138, 61, 0.22);
            }
            """
        )

        action_row = QHBoxLayout()
        action_row.addStretch(1)
        action_row.addWidget(close_btn)

        root.addWidget(title)
        root.addWidget(body)
        root.addLayout(action_row)

        popup.setStyleSheet(
            f"""
            QDialog {{
                background: {theme_tokens.COLOR_BG_MAIN};
                border: 1px solid {theme_tokens.BORDER_SUBTLE};
                border-radius: 0px;
            }}
            """
        )
        popup.adjustSize()
        required_h = popup.sizeHint().height()
        required_w = popup.sizeHint().width()
        popup.setMinimumHeight(max(popup.minimumHeight(), required_h))
        popup.resize(max(popup.minimumWidth(), required_w), max(popup.minimumHeight(), required_h))
        popup.finished.connect(lambda *_: setattr(self, "_music_empty_popup", None))
        self._music_empty_popup = popup
        popup.open()

    def _resolve_music_path(self, music_path: str | Path) -> Path | None:
        raw = str(music_path or "").strip()
        if not raw:
            return None

        candidate = Path(raw).expanduser()
        if candidate.is_absolute() and candidate.exists():
            return candidate

        clean = raw[2:] if raw.startswith("./") else raw
        rel = Path(clean)

        probes = [
            Path(resource_path(clean)),
            Path(resource_path(os.path.join("ui_ux_team/assets", clean))),
            self._music_folder / rel.name,
            self._music_folder / rel,
            Path.cwd() / rel,
            get_project_root() / rel,
        ]
        for p in probes:
            if p.exists():
                return p
        # If requested track is missing, fall back to first available track in configured folder.
        return self._first_audio_file(self._music_folder)

    def _start_player(self, real_path: Path) -> bool:
        if self._player:
            try:
                self._player.stop()
            except Exception:
                pass
            self._player = None

        player = MiniaudioPlayer(str(real_path))
        player.set_volume(self._current_volume)
        started = player.start()
        # Support both explicit bool-return players and legacy implementations.
        ok = (started is not False) and bool(player.is_playing())
        if not ok:
            return False
        self._player = player
        return True

    def handle_transcript_data(self, data: dict):
        text = TranscriptionManager.format_transcript_text(data)
        if text:
            self._transcript_win.append_segment(text)
            self._save_translation_progressive(data)
            self._save_transcript_progressive(data)

        mood_mapper_key = {
            "positive": "😊 positive",
            "neutral": "😐 neutral",
            "tense": "😠 tense",
            "unfocused": "😴 unfocused",
            "collaborative": "🤝 collaborative",
            "creative": "💡 creative",
            "unproductive": "📉 unproductive",
            "melancholic": "😢 melancholic",
            "nostalgic": "😢 nostalgic",
            "sad": "😢 sad",
        }
        mood_mapper_display = {
            "positive": "😊 Positive",
            "neutral": "😐 Neutral",
            "tense": "😠 Tense",
            "unfocused": "😴 Unfocused",
            "collaborative": "🤝 Collaborative",
            "creative": "💡 Creative",
            "unproductive": "📉 Unproductive",
            "melancholic": "😢 Melancholic",
            "nostalgic": "😢 Nostalgic",
            "sad": "😢 Sad",
        }

        mood = data.get("emotion")
        if not mood:
            return

        if mood in mood_mapper_display:
            self.mood_tag._hold_ms = 100_000
            self.mood_tag.set_queue([mood_mapper_display[mood]])
            self.float_mood(mood_mapper_display[mood])

        last_mood = getattr(self, "_last_mood", None)
        if mood == last_mood:
            return

        self._last_mood = mood
        music_path = None
        if mood in mood_mapper_key:
            music_data = self.mood_map.get(mood_mapper_key[mood])
            if music_data:
                music_path = random.choice(music_data)

        if not music_path and (self._player is None or not self._player.is_playing()):
            music_path = "ui_ux_team/assets/deep_purple_smoke_on_the_water.wav"

        if music_path:
            self.basic_music_play(music_path)

    def _save_transcript_progressive(self, data: dict):
        transcript_text = data.get("text")
        if not transcript_text:
            return

        save_dir = Path(__file__).resolve().parents[1] / "transcripts"
        save_dir.mkdir(exist_ok=True)

        filename = f"{self._current_session.replace(' ', '_').replace('[', '').replace(']', '').replace(':', '-').replace('+', '')}.txt"
        file_path = save_dir / filename

        start_sec = self.transcript_line * T_CHUNK
        end_sec = start_sec + T_CHUNK
        time_chunk = f"{self.seconds_to_hms(start_sec)} - {self.seconds_to_hms(end_sec)}"
        self.transcript_line += 1

        with open(file_path, "a", encoding="utf-8") as f:
            f.write(f"[{time_chunk}]\n{transcript_text}\n\n")

    def _save_translation_progressive(self, data: dict):
        translation_text = data.get("translation")
        if not translation_text:
            return

        save_dir = Path(__file__).resolve().parents[1] / "transcripts_translated"
        save_dir.mkdir(exist_ok=True)

        filename = f"{self._current_session.replace(' ', '_').replace('[', '').replace(']', '').replace(':', '-').replace('+', '')}_translated.txt"
        file_path = save_dir / filename

        start_sec = self.transcript_line * T_CHUNK
        end_sec = start_sec + T_CHUNK
        time_chunk = f"{self.seconds_to_hms(start_sec)} - {self.seconds_to_hms(end_sec)}"

        with open(file_path, "a", encoding="utf-8") as f:
            f.write(f"[{time_chunk}]\n{translation_text}\n\n")

    @staticmethod
    def seconds_to_hms(seconds):
        m, s = divmod(seconds, 60)
        h, m = divmod(m, 60)
        return f"{h:02d}:{m:02d}:{s:02d}"

    @staticmethod
    def load_api_key():
        from ui_ux_team.blue_ui import settings  # noqa: F401
        return os.getenv("AI_STUDIO_API_KEY")

    def open_transcript(self):
        if self._show_transcript_window is False:
            self._show_transcript_window = True
            x = self.x() + self.width()
            y = self.y()
            self._transcript_win.move(x + 10, y)
            self._transcript_win.resize(400, self.height())
            apply_native_titlebar_for_theme(self._transcript_win)
            self._transcript_win.show()
            return

        self._transcript_win.hide()
        self._show_transcript_window = False

    def record_transcript(self):
        if not self.transcription_manager:
            print("TranscriptionManager not available (check API key)")
            return

        if not self.transcription_manager.is_recording():
            self.transcription_manager.start_recording()
        else:
            self.transcription_manager.stop_recording()

    def meet_type_menu(self, parent):
        if self._meet_type is None:
            self._meet_type = FloatingMenu(parent)
            global_pos = parent.mapToGlobal(parent.rect().bottomLeft())
            self._meet_type.move(global_pos.x(), global_pos.y())
            self._meet_type.show()
            self._meet_type.closed.connect(lambda: setattr(self, "_meet_type", None))
            self._meet_type.destroyed.connect(lambda: setattr(self, "_meet_type", None))
            return

        self._meet_type.close()
        self._meet_type = None

    def settings_menu(self):
        recording_tabs = QListWidget()
        recording_tabs.addItems([f"{x} | {(y[:30].rstrip() + '...') if len(y) > 30 else y}" for x, y in get_display_names()])
        list_style = f"""
        QListWidget {{
            background: rgba(13, 19, 32, 0.35);
            color: {theme_tokens.TEXT_PRIMARY};
            border: 1px solid {theme_tokens.BORDER_SUBTLE};
            border-radius: 8px;
            padding: 4px;
        }}
        QListWidget::item {{
            padding: 8px 10px;
            border-radius: 6px;
        }}
        QListWidget::item:selected {{
            background: rgba(255, 138, 61, 0.16);
            color: #FF8A3D;
        }}
        """
        recording_tabs.setStyleSheet(list_style)

        theme_tab = QWidget()
        theme_layout = QVBoxLayout(theme_tab)
        theme_layout.setContentsMargins(8, 8, 8, 8)
        theme_layout.setSpacing(8)
        chooser = ThemeChooserMenu()
        chooser.theme_selected.connect(self._apply_theme_and_rebuild)
        theme_layout.addWidget(chooser)
        theme_layout.addStretch(1)

        music_tab = QWidget()
        music_layout = QVBoxLayout(music_tab)
        music_layout.setContentsMargins(8, 8, 8, 8)
        music_layout.setSpacing(10)
        music_label = QLabel("Music folder")
        music_label.setStyleSheet(f"color: {theme_tokens.TEXT_PRIMARY}; font-size: 14px; font-weight: 600;")
        self._music_path_edit = QLineEdit(str(self._music_folder))
        self._music_path_edit.setReadOnly(True)
        music_pick_btn = QPushButton("Choose folder")
        music_pick_btn.clicked.connect(self._pick_music_folder)
        music_pick_btn.setStyleSheet(
            """
            QPushButton {
                background: rgba(255, 138, 61, 0.14);
                color: #FF8A3D;
                border: 1px solid rgba(255, 138, 61, 0.62);
                border-radius: 8px;
                padding: 8px 12px;
                font-weight: 600;
            }
            QPushButton:hover {
                background: rgba(255, 138, 61, 0.22);
            }
            """
        )
        music_layout.addWidget(music_label)
        music_layout.addWidget(self._music_path_edit)
        music_layout.addWidget(music_pick_btn, alignment=Qt.AlignLeft)
        music_layout.addStretch(1)

        test_tab = QListWidget()
        test_tab.addItems(["test1", "test2"])
        test_tab.setStyleSheet(list_style)

        self._settings_menu = SettingsPopup(
            {
                "Recording Sources": recording_tabs,
                "Theme Selection": theme_tab,
                "Music Library": music_tab,
                "Test Tab": test_tab,
            },
            parent=self,
        )
        self._settings_menu.show_pos_size(self.pos(), self.size())

    def _pick_music_folder(self):
        selected = QFileDialog.getExistingDirectory(self, "Select Music Folder", str(self._music_folder))
        if not selected:
            return
        chosen = Path(selected).expanduser()
        if not chosen.exists():
            return
        self._music_folder = chosen
        self._music_folder.mkdir(parents=True, exist_ok=True)
        self._save_music_folder_setting(self._music_folder)
        if self._music_path_edit is not None:
            self._music_path_edit.setText(str(self._music_folder))
        self._notify_if_music_folder_empty()
        self._sync_carousel_song_items()

    def _apply_theme_and_rebuild(self, theme_key: str):
        set_theme(theme_key)
        apply_native_titlebar_for_theme(self, theme_key)
        apply_native_titlebar_for_theme(self._transcript_win, theme_key)
        self._transcript_win.refresh_theme()
        if self._bluebird_chat is not None:
            apply_native_titlebar_for_theme(self._bluebird_chat, theme_key)
            self._bluebird_chat.refresh_theme()
        if self._meet_type is not None:
            apply_native_titlebar_for_theme(self._meet_type, theme_key)
            self._meet_type.refresh_theme()
        if self.root.count():
            old_item = self.root.takeAt(0)
            old_widget = old_item.widget()
            if old_widget is not None:
                old_widget.deleteLater()
        self.root.addWidget(self.build_main_layout())
        if self._timeline is not None:
            self._timeline.refresh_theme()
        if self._settings_menu is not None:
            apply_native_titlebar_for_theme(self._settings_menu, theme_key)
            self._settings_menu.refresh_theme()

    def info_clicked(self):
        mood_items = [
            "😊 Positive",
            "😐 Neutral",
            "😠 Tense",
            "😴 Unfocused",
            "🤝 Collaborative",
            "💡 Creative",
            "📉 Unproductive",
        ]
        FloatingToast(self).show_message(random.choice(mood_items))

    def float_mood(self, mood: str):
        FloatingToast(self).show_message(mood)

    def build_sidebar(self):
        sidebar = self.color_box(theme_tokens.COLOR_SIDEBAR)
        layout = QVBoxLayout()
        layout.setContentsMargins(2, 7, 2, 12)
        layout.setSpacing(10)

        self._btn_transcript = self.button("assets/transcript_black.png", size=(60, 60))
        self._btn_transcript.setObjectName("btn_transcript")
        self._btn_transcript.clicked.connect(self.open_transcript)
        layout.addWidget(self._btn_transcript, alignment=Qt.AlignHCenter)

        self._btn_api = self.button("assets/api_black.png", size=(50, 50))
        self._btn_api.setObjectName("btn_api")
        layout.addWidget(self._btn_api, alignment=Qt.AlignHCenter)

        self._btn_info = self.button("assets/info.png", size=(50, 50))
        self._btn_info.setObjectName("btn_info")
        self._btn_info.clicked.connect(self.info_clicked)
        layout.addWidget(self._btn_info, alignment=Qt.AlignHCenter)

        self._btn_meet_type = self.button("assets/meet_type_black.png", size=(50, 50))
        self._btn_meet_type.setObjectName("btn_meet_type")
        self._btn_meet_type.clicked.connect(lambda: self.meet_type_menu(self._btn_meet_type))
        layout.addWidget(self._btn_meet_type, alignment=Qt.AlignHCenter)

        layout.addStretch(1)

        self._btn_user = self.button("assets/user_black.png", size=(60, 60))
        self._btn_user.setObjectName("btn_user")
        layout.addWidget(self._btn_user, alignment=Qt.AlignHCenter)

        self._btn_settings = self.button("assets/settings_black.png", size=(50, 50))
        self._btn_settings.setObjectName("btn_settings")
        self._btn_settings.clicked.connect(self.settings_menu)
        layout.addWidget(self._btn_settings, alignment=Qt.AlignHCenter)

        sidebar.setMinimumWidth(70)
        sidebar.setMaximumWidth(70)
        sidebar.setLayout(layout)
        return sidebar

    def build_cover_images(self):
        covers = self.color_box("transparent")
        covers.setContentsMargins(0, 0, 0, 0)
        covers.setMinimumHeight(265)
        covers.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        covers_layout = QHBoxLayout()
        covers_layout.setContentsMargins(0, 0, 0, 0)
        covers_layout.setSpacing(0)
        self._cover_carousel = SongCoverCarousel()
        self._cover_carousel.prev_requested.connect(self.prev_action)
        self._cover_carousel.current_requested.connect(self.play_click)
        self._cover_carousel.next_requested.connect(self.next_action)
        self._cover_carousel.current_song_changed.connect(self._on_cover_song_changed)
        self._sync_carousel_song_items()
        covers_layout.addWidget(self._cover_carousel, alignment=Qt.AlignCenter)
        covers.setLayout(covers_layout)

        return covers

    def _sync_carousel_song_items(self):
        if self._cover_carousel is None:
            return
        self._cover_carousel.set_song_items(self._music_tracks())

    def _on_cover_song_changed(self, song_path: str):
        selected = str(song_path or "").strip()
        if not selected:
            return

        if self._currently_playing == selected:
            return

        was_playing = bool(self._player is not None and self._player.is_playing())

        if self._player is not None and not was_playing:
            try:
                self._player.stop()
            except Exception:
                pass
            self._player = None

        self._currently_playing = selected
        if was_playing:
            self.basic_music_play(selected)
        elif self._play_btn is not None:
            self._play_btn.set_image("assets/play.png")

    def build_main_timeline(self):
        timeline_box = self.color_box("transparent")
        timeline_layout = QVBoxLayout(timeline_box)
        timeline_layout.setContentsMargins(0, 0, 0, 0)
        timeline_layout.setSpacing(0)

        self._timeline = PlaybackTimeline()
        self._timeline.setFixedHeight(52)
        self._timeline.seek_requested.connect(self._on_timeline_seek)
        self._timeline.set_duration(self._timeline_dummy_duration)
        self._timeline.set_position(self._timeline_dummy_position)
        timeline_layout.addWidget(self._timeline)

        self._sync_timeline_from_player()
        return timeline_box

    def build_timeline_volume_section(self):
        return self.build_main_timeline()

    def play_click(self, file_path=None):
        file_path = file_path or self._currently_playing

        if self._player is None:
            real_path = self._resolve_music_path(file_path)
            if real_path is None:
                print(f"Music file not found for input: {file_path}")
                self._play_btn.set_image("assets/play.png")
                return
            if not self._start_player(real_path):
                self._play_btn.set_image("assets/play.png")
                return
            self._play_btn.set_image("assets/pause.png")
            if self._timeline is not None:
                duration = self._player.duration_seconds() if hasattr(self._player, "duration_seconds") else 0.0
                position = self._player.position_seconds() if hasattr(self._player, "position_seconds") else 0.0
                self._timeline.set_duration(duration)
                self._timeline.set_position(position)
            return

        if self._player.paused:
            resumed = self._player.start()
            if resumed is False:
                self._play_btn.set_image("assets/play.png")
                self._player = None
                return
            self._play_btn.set_image("assets/pause.png")
        else:
            self._player.pause()
            self._play_btn.set_image("assets/play.png")

    def build_main_controls(self):
        control_layer = QHBoxLayout()
        control_layer.setContentsMargins(10, 0, 10, 10)
        control_layer.setAlignment(Qt.AlignTop | Qt.AlignHCenter)
        controls = self.color_box("transparent")
        controls.setFixedWidth(290)
        controls.setMaximumHeight(100)
        controls.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        controls.setLayout(control_layer)

        self._btn_prev = self.button("assets/prev.png", size=(35, 35))
        self._btn_prev.setObjectName("btn_prev")
        self._btn_prev.clicked.connect(self.prev_action)
        self._play_btn = self.button("assets/play.png", size=(80, 80))
        self._play_btn.setObjectName("btn_play")
        self._play_btn.clicked.connect(self.play_click)
        self._btn_next = self.button("assets/next.png", size=(35, 35))
        self._btn_next.setObjectName("btn_next")
        self._btn_next.clicked.connect(self.next_action)

        control_layer.addWidget(self._btn_prev, 0, Qt.AlignVCenter)
        control_layer.addWidget(self._play_btn, 0, Qt.AlignVCenter)
        control_layer.addWidget(self._btn_next, 0, Qt.AlignVCenter)

        return controls

    def prev_action(self):
        if self._cover_carousel is not None:
            self._cover_carousel.step_prev()

    def next_action(self):
        if self._cover_carousel is not None:
            self._cover_carousel.step_next()

    def open_bluebird_chat(self):
        if self._bluebird_chat is None:
            transcript_text = self._transcript_win.text_box.toPlainText()
            api_key = self.load_api_key()
            self._bluebird_chat = BlueBirdChatView(api_key=api_key, initial_transcript=transcript_text)
            self._bluebird_chat.closed.connect(lambda: setattr(self, "_bluebird_chat", None))
            x = self.x() - 400
            y = self.y()
            self._bluebird_chat.move(x - 10, y)
            self._bluebird_chat.resize(400, self.height())
            apply_native_titlebar_for_theme(self._bluebird_chat)
            self._bluebird_chat.show()
            return

        self._bluebird_chat.close()
        self._bluebird_chat = None

    def build_blue_bird(self):
        self._btn_bluebird = self.button("assets/blue_bird.png", size=(70, 70))
        self._btn_bluebird.setObjectName("btn_bluebird")
        self._btn_bluebird.clicked.connect(self.open_bluebird_chat)
        return self._btn_bluebird

    def set_volume(self, volume):
        self._current_volume = volume
        if self._player:
            self._player.set_volume(volume)

    def _on_timeline_seek(self, target_seconds: float):
        self._timeline_seek_lock_until = time.monotonic() + 0.25
        if self._player is None:
            self._timeline_dummy_position = max(0.0, min(self._timeline_dummy_duration, target_seconds))
            if self._timeline is not None:
                self._timeline.set_duration(self._timeline_dummy_duration)
                self._timeline.set_position(self._timeline_dummy_position)
            return
        if hasattr(self._player, "seek"):
            was_playing = self._player.is_playing() if hasattr(self._player, "is_playing") else False
            seek_ok = self._player.seek(target_seconds)
            if seek_ok is False:
                self._play_btn.set_image("assets/play.png")
                self._player = None
                return
            if was_playing and hasattr(self._player, "is_playing") and not self._player.is_playing():
                resumed = self._player.start()
                if resumed is False or not self._player.is_playing():
                    self._play_btn.set_image("assets/play.png")
                    self._player = None
                    return
        if self._timeline is not None:
            position = self._player.position_seconds() if hasattr(self._player, "position_seconds") else target_seconds
            self._timeline.set_position(position)

    def _sync_timeline_from_player(self):
        if self._timeline is None:
            return
        if self._timeline.is_interacting():
            return
        if time.monotonic() < self._timeline_seek_lock_until:
            return
        if self._player is None:
            self._timeline.set_duration(self._timeline_dummy_duration)
            self._timeline.set_position(self._timeline_dummy_position)
            return
        duration = self._player.duration_seconds() if hasattr(self._player, "duration_seconds") else 0.0
        position = self._player.position_seconds() if hasattr(self._player, "position_seconds") else 0.0
        self._timeline.set_duration(duration)
        self._timeline.set_position(position)

    def build_main_bottom_panel(self):
        bottom_con = self.color_box("transparent")
        bottom_layout = QVBoxLayout()
        bottom_layout.setContentsMargins(10, 10, 10, 10)
        bottom_layout.setSpacing(4)
        bottom_con.setLayout(bottom_layout)

        controls = self.build_main_controls()
        controls.setFixedHeight(100)

        # Top row: controls centered, volume on the right, aligned to top.
        slot_width = 180
        slot_height = 100

        top_row = QHBoxLayout()
        top_row.setContentsMargins(0, 0, 0, 0)
        top_row.setSpacing(0)

        left_placeholder = QWidget()
        left_placeholder.setFixedSize(slot_width, slot_height)

        self._volume_control = IntegratedVolumeControl(initial_volume=self._current_volume)
        self._volume_control.volume_changed.connect(self.set_volume)

        volume_slot = QWidget()
        volume_slot.setFixedSize(slot_width, slot_height)
        volume_layout = QHBoxLayout(volume_slot)
        volume_layout.setContentsMargins(0, 0, 0, 0)
        volume_layout.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        volume_layout.addWidget(self._volume_control, alignment=Qt.AlignLeft | Qt.AlignTop)

        # Deterministic order: [spacer][controls][volume]
        top_row.addStretch(1)
        top_row.addWidget(left_placeholder, alignment=Qt.AlignTop)
        top_row.addWidget(controls, alignment=Qt.AlignTop)
        top_row.addWidget(volume_slot, alignment=Qt.AlignTop)
        top_row.addStretch(1)

        # Bottom row: bird anchored bottom-left as its own layout.
        bottom_row = QHBoxLayout()
        bottom_row.setContentsMargins(0, 0, 0, 0)
        bottom_row.setSpacing(0)

        blue_bird = self.build_blue_bird()
        bottom_row.addWidget(blue_bird, alignment=Qt.AlignLeft | Qt.AlignBottom)
        bottom_row.addStretch(1)

        bottom_layout.addLayout(top_row, 1)
        bottom_layout.addLayout(bottom_row, 0)

        return bottom_con

    def build_main_panel(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        mood_items = [
            "😊 Positive",
            "😐 Neutral",
            "😠 Tense",
            "😴 Unfocused",
            "🤝 Collaborative",
            "💡 Creative",
            "📉 Unproductive",
        ]

        self.mood_tag = QueuedMarqueeLabel(mood_items, hold_ms=3200, fade_ms=220, step=1, interval_ms=25, gap=60)
        font = QFont()
        font.setPointSize(20)
        self.mood_tag.label.setFont(font)
        self.mood_tag.setMaximumHeight(30)

        layout.addWidget(self.mood_tag)
        layout.addWidget(self.build_cover_images(), 1)
        layout.addWidget(self.build_timeline_volume_section())
        layout.addWidget(self.build_main_bottom_panel())

        main_box = self.color_box(theme_tokens.COLOR_BG_MAIN)
        main_box.setLayout(layout)
        return main_box

    @staticmethod
    def color_box(color):
        box = QFrame()
        if isinstance(color, str) and color.startswith("rgba("):
            box.setStyleSheet(f"background-color: {color}; border: none;")
            box.setAutoFillBackground(False)
        elif color == "transparent":
            box.setStyleSheet("background-color: transparent; border: none;")
            box.setAutoFillBackground(False)
        else:
            box.setAutoFillBackground(True)
            pal = box.palette()
            pal.setColor(QPalette.Window, QColor(color))
            box.setPalette(pal)
        return box

    @staticmethod
    def build_path(file_path):
        if file_path.startswith("assets/"):
            file_path = file_path.split("assets/", 1)[1]
        return os.path.join(BASE, file_path)

    @staticmethod
    def button(file_path="", size=(40, 40)):
        return ImageButton(path=MainUI.build_path(file_path), size=size, fallback=IMAGE_NOT_FOUND)

    @staticmethod
    def image_box(file_path):
        label = QLabel()
        label.setScaledContents(True)
        label.setMinimumSize(50, 50)

        pix = QPixmap(MainUI.build_path(file_path))
        label.setPixmap(QPixmap(IMAGE_NOT_FOUND) if pix.isNull() else pix)
        return label

    def build_main_layout(self):
        h = QHBoxLayout()
        h.setContentsMargins(0, 0, 0, 0)
        h.setSpacing(0)

        h.addWidget(self.build_main_panel(), 4)
        h.addWidget(self.build_sidebar(), 1)

        container = QWidget()
        container.setLayout(h)
        return container


MainWindowView = MainUI


if __name__ == "__main__":
    app = QApplication(sys.argv)
    icon = _resolve_window_icon()
    if icon is not None:
        app.setWindowIcon(icon)
    window = MainUI()
    window.show()
    raise SystemExit(app.exec())
