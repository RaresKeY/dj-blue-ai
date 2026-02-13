import json
import os
import random
import sys
from pathlib import Path

from PySide6.QtCore import Qt, Signal, QPoint
from PySide6.QtGui import QPalette, QColor, QPixmap, QFont
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QVBoxLayout,
    QWidget,
)

from architects.helpers.managed_mem import ManagedMem
from architects.helpers.miniaudio_player import MiniaudioPlayer
from architects.helpers.resource_path import resource_path
from architects.helpers.tabs_audio import get_display_names
from architects.helpers.transcription_manager import TranscriptionManager
from ui_ux_team.blue_ui.views.chat_window import BlueBirdChatView
from ui_ux_team.blue_ui.views.settings_popup import FloatingMenu, SettingsPopup
from ui_ux_team.blue_ui.views.transcript_window import TranscriptWindowView
from ui_ux_team.blue_ui.widgets.image_button import ImageButton, IMAGE_NOT_FOUND
from ui_ux_team.blue_ui.widgets.marquee import QueuedMarqueeLabel
from ui_ux_team.blue_ui.widgets.toast import FloatingToast
from ui_ux_team.blue_ui.widgets.volume import VolumeButton, VolumePopup


def get_project_root() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parents[3]


COLOR_BG_MAIN = "#1E1E1E"
COLOR_SIDEBAR = "#2A0A3C"
COLOR_COVERS_BG = "#1E1E1E"
COLOR_TIMELINE_BG = "#2A2A2A"
COLOR_BOTTOM_BG = "#1E1E1E"
COLOR_CONTROLS_BG = "#1E1E1E"

BASE = resource_path("ui_ux_team/prototype_r")
T_CHUNK = 30


class MainUI(QWidget):
    transcript_ready = Signal(dict)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("DJ Blue UI")
        self.resize(721, 487)

        self._play_btn = None
        self._player = None
        self._paused = False
        self._currently_playing = "deep_purple_smoke_on_the_water.wav"
        self._current_volume = 0.8

        self.transcription_manager = None
        self.transcript_line = 0

        self.root = QVBoxLayout(self)
        self.root.setContentsMargins(0, 0, 0, 0)
        self.root.addWidget(self.build_main_layout())

        self.man_mem = ManagedMem()
        music_folder = get_project_root() / "mood_music_collection"
        music_folder.mkdir(parents=True, exist_ok=True)

        mood_data_path = resource_path("mood_readers/data/mood_playlists_organized.json")
        with open(mood_data_path, "r", encoding="utf-8") as f:
            self.mood_map = json.load(f)

        self._transcript_win = TranscriptWindowView(parent=self)
        self._transcript_win.closed.connect(lambda: setattr(self, "_show_transcript_window", False))
        self._transcript_win.record_clicked.connect(self.record_transcript)
        self._show_transcript_window = False

        self._current_session_segments = []
        self._current_session = f"SESSION [{self.man_mem.timestamp_helper()}]"

        self.transcript_ready.connect(self.handle_transcript_data)

        self._bluebird_chat = None
        self._settings_menu = None
        self._meet_type = None
        self._volume_popup = None

        api_key = self.load_api_key()
        if api_key:
            self.transcription_manager = TranscriptionManager(api_key, chunk_seconds=T_CHUNK)
            self.transcription_manager.set_callback(self.transcript_ready.emit)
        else:
            print("Missing API Key, TranscriptionManager not initialized")

    def basic_music_play(self, music_path):
        clean_path = music_path[2:] if music_path.startswith("./") else music_path
        real_path = Path(resource_path(clean_path))
        if not real_path.exists():
            real_path = Path(resource_path(os.path.join("ui_ux_team/prototype_r", clean_path)))
        if not real_path.exists():
            print(f"Music file not found: {real_path}")
            return

        if self._player and self._currently_playing == music_path and self._player.is_playing():
            return

        if self._player:
            self._player.stop()

        self._currently_playing = music_path
        self._play_btn.set_image("assets/pause.png")
        self._player = MiniaudioPlayer(str(real_path))
        self._player.set_volume(self._current_volume)
        self._player.start()

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
            music_path = "ui_ux_team/prototype_r/deep_purple_smoke_on_the_water.wav"

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

        test_tab = QListWidget()
        test_tab.addItems(["test1", "test2"])

        self._settings_menu = SettingsPopup({"Recording Sources": recording_tabs, "Test Tab": test_tab}, parent=self)
        self._settings_menu.show_pos_size(self.pos(), self.size())

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
        sidebar = self.color_box(COLOR_SIDEBAR)
        layout = QVBoxLayout()
        layout.setContentsMargins(2, 7, 2, 7)
        layout.setSpacing(10)

        transcript_button = self.button("assets/transcript_black.png", size=(60, 60))
        transcript_button.clicked.connect(self.open_transcript)
        layout.addWidget(transcript_button, alignment=Qt.AlignHCenter)

        api_button = self.button("assets/api_black.png", size=(50, 50))
        layout.addWidget(api_button, alignment=Qt.AlignHCenter)

        info_button = self.button("assets/info.png", size=(50, 50))
        info_button.clicked.connect(self.info_clicked)
        layout.addWidget(info_button, alignment=Qt.AlignHCenter)

        meet_type = self.button("assets/meet_type_black.png", size=(50, 50))
        meet_type.clicked.connect(lambda: self.meet_type_menu(meet_type))
        layout.addWidget(meet_type, alignment=Qt.AlignHCenter)

        layout.addStretch(1)

        user_button = self.button("assets/user_black.png", size=(60, 60))
        layout.addWidget(user_button, alignment=Qt.AlignHCenter)

        settings_button = self.button("assets/settings_black.png", size=(50, 50))
        settings_button.clicked.connect(self.settings_menu)
        layout.addWidget(settings_button, alignment=Qt.AlignHCenter)

        sidebar.setMinimumWidth(70)
        sidebar.setMaximumWidth(70)
        sidebar.setLayout(layout)
        return sidebar

    def build_cover_images(self):
        covers = self.color_box(COLOR_COVERS_BG)
        covers.setContentsMargins(0, 0, 0, 0)
        covers.setMinimumSize(500, 200)

        covers_layout = QHBoxLayout()
        covers_images = [self.image_box("") for _ in range(3)]
        for i, box in enumerate(covers_images):
            box.setMinimumSize(50, 50)
            box.setMaximumSize(180 if i == 1 else 120, 180 if i == 1 else 120)
            covers_layout.addWidget(box)
        covers.setLayout(covers_layout)

        return covers

    def build_main_timeline(self):
        timeline_box = self.color_box(COLOR_TIMELINE_BG)
        timeline_box.setFixedHeight(15)
        return timeline_box

    def play_click(self, file_path=None):
        file_path = file_path or self._currently_playing

        if self._player is None:
            self._play_btn.set_image("assets/pause.png")
            clean_path = file_path[2:] if file_path.startswith("./") else file_path
            real_path = Path(resource_path(clean_path))
            if not real_path.exists():
                real_path = Path(resource_path(os.path.join("ui_ux_team/prototype_r", clean_path)))

            self._player = MiniaudioPlayer(str(real_path))
            self._player.set_volume(self._current_volume)
            self._player.start()
            return

        if self._player.paused:
            self._player.start()
            self._play_btn.set_image("assets/pause.png")
        else:
            self._player.pause()
            self._play_btn.set_image("assets/play.png")

    def build_main_controls(self):
        control_layer = QHBoxLayout()
        control_layer.setContentsMargins(10, 10, 10, 10)
        controls = self.color_box(COLOR_CONTROLS_BG)
        controls.setMaximumHeight(100)
        controls.setLayout(control_layer)

        prev_btn = self.button("assets/prev.png", size=(35, 35))
        self._play_btn = self.button("assets/play.png", size=(80, 80))
        self._play_btn.clicked.connect(self.play_click)
        next_btn = self.button("assets/next.png", size=(35, 35))

        control_layer.addWidget(prev_btn)
        control_layer.addWidget(self._play_btn)
        control_layer.addWidget(next_btn)

        return controls

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
            self._bluebird_chat.show()
            return

        self._bluebird_chat.close()
        self._bluebird_chat = None

    def build_blue_bird(self):
        blue_bird = self.button("assets/blue_bird.png", size=(70, 70))
        blue_bird.clicked.connect(self.open_bluebird_chat)
        right_spacer = QWidget()
        right_spacer.setFixedSize(70, 70)
        return blue_bird, right_spacer

    def on_volume_start(self):
        button = self.sender()
        if not button:
            return

        current_vol = self._player._volume if self._player else 1.0

        if not self._volume_popup:
            self._volume_popup = VolumePopup(parent=button, current_volume=current_vol)
            self._volume_popup.volume_changed.connect(self.set_volume)
            self._volume_popup.closed.connect(lambda: setattr(self, "_volume_popup", None))

        self._volume_popup.show()
        popup_w = self._volume_popup.width()
        popup_h = self._volume_popup.height()
        local_offset = QPoint((button.width() - popup_w) // 2 + button.width() // 2, -popup_h - 10)
        self._volume_popup.move(button.mapToGlobal(local_offset))

    def on_volume_move(self, global_pos):
        if self._volume_popup and self._volume_popup.isVisible():
            slider = self._volume_popup.slider
            local_pos = slider.mapFromGlobal(global_pos)
            h = slider.height()
            y = max(0, min(h, local_pos.y()))
            ratio = 1.0 - (y / h) if h > 0 else 0.0
            slider.setValue(int(ratio * slider.maximum()))

    def on_volume_end(self):
        if self._volume_popup:
            self._volume_popup.close()
            self._volume_popup = None

    def set_volume(self, volume):
        self._current_volume = volume
        if self._player:
            self._player.set_volume(volume)

    def build_main_bottom_panel(self):
        bottom_con = self.color_box(COLOR_BOTTOM_BG)
        bottom_layout = QHBoxLayout()
        bottom_con.setLayout(bottom_layout)

        blue_bird, _ = self.build_blue_bird()

        volume_control = VolumeButton(path=MainUI.build_path("assets/volume_button.png"), size=(42, 42), fallback=IMAGE_NOT_FOUND)
        volume_control.interaction_start.connect(self.on_volume_start)
        volume_control.interaction_move.connect(self.on_volume_move)
        volume_control.interaction_end.connect(self.on_volume_end)

        right_spacer = QWidget()
        right_spacer.setFixedSize(70, 70)
        right_layout = QHBoxLayout(right_spacer)
        right_layout.setContentsMargins(5, 5, 5, 5)
        right_layout.addWidget(volume_control, alignment=Qt.AlignTop | Qt.AlignRight)

        controls = self.build_main_controls()

        bottom_layout.addWidget(blue_bird, alignment=Qt.AlignBottom)
        bottom_layout.addWidget(controls, alignment=Qt.AlignHCenter | Qt.AlignTop)
        bottom_layout.addWidget(right_spacer, alignment=Qt.AlignTop)

        return bottom_con

    def build_main_panel(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

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
        layout.addWidget(self.build_cover_images(), alignment=Qt.AlignCenter | Qt.AlignBottom)
        layout.addWidget(self.build_main_timeline())
        layout.addWidget(self.build_main_bottom_panel())

        main_box = self.color_box(COLOR_BG_MAIN)
        main_box.setLayout(layout)
        return main_box

    @staticmethod
    def color_box(color):
        box = QFrame()
        box.setAutoFillBackground(True)
        pal = box.palette()
        pal.setColor(QPalette.Window, QColor(color))
        box.setPalette(pal)
        return box

    @staticmethod
    def build_path(file_path):
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
    window = MainUI()
    window.show()
    raise SystemExit(app.exec())
