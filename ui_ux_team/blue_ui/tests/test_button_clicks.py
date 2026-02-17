import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

from ui_ux_team.blue_ui.views.main_window import MainUI


os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


class _FakePlayer:
    def __init__(self, *_args, **_kwargs):
        self.paused = False
        self._playing = False
        self._volume = 0.8

    def set_volume(self, volume):
        self._volume = volume

    def start(self):
        self.paused = False
        self._playing = True

    def pause(self):
        self.paused = True
        self._playing = False

    def stop(self):
        self._playing = False

    def is_playing(self):
        return self._playing


class TestBlueUIButtonClicks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        patcher = patch("ui_ux_team.blue_ui.views.main_window.MiniaudioPlayer", _FakePlayer)
        self.addCleanup(patcher.stop)
        patcher.start()

        self.window = MainUI()
        self._tmp_music_dir = tempfile.TemporaryDirectory()
        Path(self._tmp_music_dir.name, "test_track.wav").touch()
        self.window._music_folder = Path(self._tmp_music_dir.name)
        self.window.show()

    def tearDown(self):
        if self.window._settings_menu is not None:
            self.window._settings_menu.close()
        if self.window._meet_type is not None:
            self.window._meet_type.close()
        if self.window._bluebird_chat is not None:
            self.window._bluebird_chat.close()
        if self.window._profile_window is not None:
            self.window._profile_window.close()
        self.window._transcript_win.close()
        self.window.close()
        self._tmp_music_dir.cleanup()

    def _click(self, widget):
        self.assertIsNotNone(widget)
        QTest.mouseClick(widget, Qt.LeftButton)
        self.app.processEvents()

    def test_sidebar_buttons_click_without_crash(self):
        self._click(self.window._btn_transcript)
        self.assertTrue(self.window._show_transcript_window)
        self._click(self.window._btn_transcript)
        self.assertFalse(self.window._show_transcript_window)

        self._click(self.window._btn_info)

        self._click(self.window._btn_meet_type)
        self.assertIsNotNone(self.window._meet_type)
        self._click(self.window._btn_meet_type)
        self.assertIsNone(self.window._meet_type)

        self._click(self.window._btn_settings)
        self.assertIsNotNone(self.window._settings_menu)

        self._click(self.window._btn_api)
        self._click(self.window._btn_user)
        self.assertIsNotNone(self.window._profile_window)
        self._click(self.window._btn_user)
        self.assertIsNone(self.window._profile_window)

    def test_transport_buttons_click_without_crash(self):
        self.assertIsNone(self.window._player)

        self._click(self.window._play_btn)
        self.assertIsNotNone(self.window._player)
        self.assertFalse(self.window._player.paused)

        self._click(self.window._play_btn)
        self.assertTrue(self.window._player.paused)

        self._click(self.window._btn_prev)
        self._click(self.window._btn_next)

    def test_bluebird_button_toggles_chat(self):
        self._click(self.window._btn_bluebird)
        self.assertIsNotNone(self.window._bluebird_chat)

        self._click(self.window._btn_bluebird)
        self.assertIsNone(self.window._bluebird_chat)


if __name__ == "__main__":
    unittest.main()
