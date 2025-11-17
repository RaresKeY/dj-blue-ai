import json
import os

from pathlib import Path
from helpers.managed_mem import ManagedMem 

# TODO: create custom json rules for save if necessary in managed mem

class Song():
    def __init__(self, song_filepath):
        # Required
        self.filepath: Path = song_filepath
        self.mood_tags: list[str] = None
        self.camelot_tags: list[str] = None
        self.tempo: int = None

        # Managed Mem Singleton
        self.mem_man = ManagedMem()

        # Optional
        self.duration: float = None
        self.bitrate: int = None

        data = self._read_data(song_filepath)

        if not data:
            # generate and save
            pass

    def _read_data(self, song_filepath):
        """ read filepath key value from managed mem """
        return self.mem_man.gettr(song_filepath)
    
    def _write_data(self, song_filepath):
        """ generate and write self in managed mem, key is filepath """

        # Required
        self._get_tags()
        self._get_camelot()
        self._get_tempo()

        # Optional
        self._get_duration()

        self.mem_man.settr(song_filepath, self)

    def _get_tags(self):
        # read music librarians tag list (use managed mem?)
        pass

    def _get_camelot(self):
        # use mood readers script to determine camelot
        pass

    def _get_tempo(self):
        # use mood readers script to determine tempo
        pass

    def _get_duration(self):
        # use pyaudio to get duration (could be useful for queue operations)
        pass
