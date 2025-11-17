import json
import os
import tempfile
import unittest
from pathlib import Path

from architects.helpers.managed_mem import ManagedMem
from architects.song import Song


class SongManagedMemTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tempdir.cleanup)
        self._original_file = ManagedMem._file
        ManagedMem._file = os.path.join(self.tempdir.name, "managed_mem.json")
        ManagedMem._instance = None
        self.addCleanup(self._restore_managed_mem_class)
        self.mem = ManagedMem()

    def _restore_managed_mem_class(self):
        ManagedMem._instance = None
        ManagedMem._file = self._original_file

    def _build_song(self, filepath: Path) -> Song:
        song = Song(filepath)
        song.mood_tags = ["energetic", "uplifting"]
        song.camelot_tags = ["8B"]
        song.tempo = 128
        song.duration = 3.5
        song.bitrate = 320
        song._write_data(song.filepath)
        return song

    def test_write_and_restore_song_roundtrip(self):
        filepath = Path(self.tempdir.name) / "club_track.wav"
        storage_key = str(filepath)
        song = self._build_song(filepath)

        song._write_data(storage_key)
        self.mem.flush()

        ManagedMem._instance = None
        mem_reloaded = ManagedMem()
        reloaded_song = mem_reloaded.gettr(storage_key)

        self.assertIsInstance(reloaded_song, Song)
        self.assertEqual(reloaded_song.filepath, song.filepath)
        self.assertEqual(reloaded_song.mood_tags, song.mood_tags)
        self.assertEqual(reloaded_song.camelot_tags, song.camelot_tags)
        self.assertEqual(reloaded_song.tempo, song.tempo)
        self.assertEqual(reloaded_song.duration, song.duration)
        self.assertEqual(reloaded_song.bitrate, song.bitrate)

    def test_json_snapshot_contains_song_payload(self):
        filepath = Path(self.tempdir.name) / "ambient.wav"
        storage_key = str(filepath)
        song = self._build_song(filepath)

        song._write_data(storage_key)
        self.mem.flush()

        with open(ManagedMem._file, "r", encoding="utf-8") as fh:
            data = json.load(fh)

        self.assertIn(storage_key, data)
        payload = data[storage_key]
        self.assertEqual(payload["__type__"], "Song")
        self.assertEqual(payload["state"]["filepath"], str(song.filepath))
        self.assertEqual(payload["state"]["mood_tags"], song.mood_tags)

    def test_read_data_returns_value_from_managed_mem(self):
        storage_key = str(Path(self.tempdir.name) / "existing.wav")
        expected_value = {"tempo": 110}
        self.mem.settr(storage_key, expected_value)

        song = Song(storage_key)
        result = song._read_data(storage_key)

        self.assertEqual(result, expected_value)


if __name__ == "__main__":
    unittest.main()
